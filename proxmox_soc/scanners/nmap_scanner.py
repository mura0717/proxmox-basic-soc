#!/usr/bin/env python3
"""
Nmap Scanner 
"""
import os
import sys
import subprocess
import nmap
import hashlib
from datetime import datetime, timezone
from typing import List, Dict, Optional

from proxmox_soc.debug.tools.asset_debug_logger import debug_logger
from proxmox_soc.debug.categorize_from_logs.nmap_categorize_from_logs import nmap_debug_categorization
from proxmox_soc.config.network_config import NMAP_SCAN_RANGES
from proxmox_soc.config.nmap_profiles import SCAN_PROFILES
from proxmox_soc.utils.mac_utils import normalize_mac

DNS_SERVERS = os.getenv('NMAP_DNS_SERVERS', '').strip()
DNS_ARGS = f"--dns-servers {DNS_SERVERS} -R" if DNS_SERVERS else "-R"
NO_ROOT_COMMANDS = ['web', 'list', 'help']
COMMAND = sys.argv[1] if len(sys.argv) > 1 else 'discovery'
IS_CATEGORIZATION_DEBUG = os.getenv('NMAP_CATEGORIZATION_DEBUG', '0') == '1'

# Auto-elevate to root for scan commands if NOT in categorization debug mode.
if not IS_CATEGORIZATION_DEBUG and COMMAND not in NO_ROOT_COMMANDS:
    if os.geteuid() != 0:
        user_euid = os.geteuid()
        command_to_run = ['sudo', sys.executable] + sys.argv
        print(f"\nDEBUG: The exact command being passed to sudo is: {' '.join(command_to_run)}\nThe user euid is: {user_euid}\n")
        
        cmd = ['sudo', '-n', sys.executable, '-c', 'exit(0)']
        result = subprocess.run(cmd, capture_output=True, timeout=5)
        can_sudo = result.returncode == 0

        if can_sudo:
            try:
                print("Attempting to elevate to root privileges for scan...")
                subprocess.run(['sudo', sys.executable] + sys.argv, check=True)
                sys.exit(0)
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"\nERROR: Failed to auto-elevate even with passwordless sudo rights: {e}")
                sys.exit(1)
        else:
            print("\nERROR: Root privileges are required for this scan.")
            print("This script cannot auto-elevate because 'sudo' requires a password.")
            print(f"Please run it manually with: sudo {sys.executable} {' '.join(sys.argv)}")
            sys.exit(1)

class NmapScanner:
    """Nmap Scanner with predefined scan profiles and Snipe-IT integration"""
    
    def __init__(self, network_ranges: Optional[List[str]] = None):
        if network_ranges is None:
            self.network_ranges = NMAP_SCAN_RANGES
        else:
            self.network_ranges = network_ranges
        self.nm = nmap.PortScanner()
    
    def run_scan(self, profile: str = 'discovery', targets: Optional[List[str]] = None) -> List[Dict]:
        """Run Nmap scan with specified profile"""
        
        if profile not in SCAN_PROFILES:
            print(f"Unknown profile: {profile}")
            return []
        
        scan_config = SCAN_PROFILES[profile]
        args = scan_config['args']
        if scan_config.get('use_dns'):
            args = f"{args} {DNS_ARGS}"
        scan_targets = ' '.join(targets) if targets else ' '.join(self.network_ranges)
        
        print(f"Running {profile} scan: {scan_config['description']}")
        print(f"Targets: {scan_targets}")
        
        try:
            self.nm.scan(hosts=scan_targets, arguments=scan_config['args'])
            
            assets = []
            for host in self.nm.all_hosts():
                if self.nm[host].state() == 'up':
                    asset = self._parse_host(host, profile, scan_config)
                    assets.append(asset)
            
            return assets
            
        except nmap.PortScannerError as e:
            print(f"Nmap error: {e}")
            return []
        except Exception as e:
            print(f"Scan failed: {e}")
            return []
    
    def _parse_host(self, host: str, profile: str, scan_config: Dict) -> Dict:
        """
        Parse Nmap results for a single host to collect raw data.
        Categorization logic is handled later by the AssetCategorizer.
        """
        nmap_host = self.nm[host]
        
        # Log raw nmap data for debugging before parsing.
        raw_host_data = {
            'host': host,
            'hostname': nmap_host.hostname(),
            'state': nmap_host.state(),
            'addresses': nmap_host.get('addresses', {}),
            'vendor': nmap_host.get('vendor', {}),
            'osmatch': nmap_host.get('osmatch', []),
            'protocols': {}
        }
        for proto in nmap_host.all_protocols():
            raw_host_data['protocols'][proto] = nmap_host[proto]
        
        debug_logger.log_raw_host_data('nmap', host, raw_host_data)
        
        asset = {
            'last_seen_ip': host,
            'nmap_last_scan': datetime.now(timezone.utc).isoformat(),
            'nmap_scan_profile': profile,
            'name': nmap_host.hostname() or f"Device-{host}",
            'dns_hostname': nmap_host.hostname(),
            '_source': 'nmap',
            'mac_addresses': None,
            'manufacturer': None,
            'os_platform': None,
            'nmap_os_guess': None,
            'os_accuracy': None,
            'nmap_open_ports': None,
            'open_ports_hash': None,
            'nmap_services': [],
        }
        
        mac_addresses = []
        if 'mac' in nmap_host.get('addresses', {}):
            raw_mac = nmap_host['addresses']['mac']
            normalized_mac = normalize_mac(raw_mac)
            if normalized_mac:
                mac_addresses.append(normalized_mac)
                asset['mac_addresses'] = normalized_mac
                if 'vendor' in nmap_host and nmap_host['vendor']:
                    asset['manufacturer'] = list(nmap_host['vendor'].values())[0]
        
        if scan_config.get('collects_ports') and 'osmatch' in nmap_host and nmap_host['osmatch']:
            os_match = nmap_host['osmatch'][0]
            asset['nmap_os_guess'] = os_match.get('name', '')
            asset['os_accuracy'] = os_match.get('accuracy')
            asset['os_platform'] = os_match.get('name', '')
        
        if scan_config.get('collects_ports'):
            open_ports_list = []
            service_names = []
            
            for proto in nmap_host.all_protocols():
                for port, port_info in nmap_host[proto].items():
                    if port_info.get('state') == 'open':
                        service_name = port_info.get('name', 'unknown')
                        service_names.append(service_name)
                        
                        product = port_info.get('product', '')
                        version = port_info.get('version', '')

                        port_str = f"{port}/{proto}/{service_name} ({product} {version})".strip()
                        open_ports_list.append(port_str)
            
            if open_ports_list:
                asset['nmap_open_ports'] = '\n'.join(sorted(open_ports_list))
                asset['open_ports_hash'] = hashlib.md5(asset['nmap_open_ports'].encode()).hexdigest()
                asset['nmap_services'] = service_names
                
        asset['first_seen_date'] = datetime.now(timezone.utc).isoformat()
        return {k: v for k, v in asset.items() if v is not None and v != '' and v != []}
    
    def scan_network(self, profile: str = 'discovery') -> Dict:
        """Run scan and sync to Snipe-IT"""
        print(f"Starting Nmap {profile} scan...")
        
        self.asset_matcher.clear_all_caches()
        
        assets = self.run_scan(profile)
        
        if not assets:
            print("No hosts found.")
            print(f"Found {len(assets)} hosts")
        
        debug_logger.log_parsed_asset_data('nmap', assets)  
        results = self.asset_matcher.process_scan_data('nmap', assets)
        debug_logger.log_sync_summary('nmap', results)
        
        print(f"Sync complete: {results['created']} created, {results['updated']} updated")
        return results

def main():
        # If categorization debug is on, just run that and exit.
    if nmap_debug_categorization.debug: 
        nmap_debug_categorization.write_nmap_assets_to_logfile()
        return

    debug_logger.clear_logs('nmap')
    
    scanner = NmapScanner()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command in SCAN_PROFILES:
            scanner.scan_network(command)
        elif command == 'list':
            print("\nAvailable scan profiles:")
            for name, config in SCAN_PROFILES.items():
                print(f"  {name:12} - {config['description']}")
        else:
            print(f"Unknown command: {command}")
            print("Usage: nmap_scanner.py [profile_name|list]")
    else:
        scanner.scan_network('discovery')

if __name__ == "__main__":
    main()