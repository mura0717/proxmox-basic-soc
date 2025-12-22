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

from proxmox_soc.snipe_it.snipe_scripts.cache.clear_cache import SnipeCacheClearer
from proxmox_soc.debug.tools.asset_debug_logger import debug_logger
from proxmox_soc.debug.categorize_from_logs.nmap_categorize_from_logs import nmap_debug_categorization
from proxmox_soc.config.network_config import NMAP_SCAN_RANGES
from proxmox_soc.config.nmap_profiles import NMAP_SCAN_PROFILES
from proxmox_soc.utils.mac_utils import normalize_mac
from proxmox_soc.utils.sudo_utils import elevate_to_root

DNS_SERVERS = os.getenv('NMAP_DNS_SERVERS', '').strip()
DNS_ARGS = f"--dns-servers {DNS_SERVERS} -R" if DNS_SERVERS else "-R"

class NmapScanner:
    """Nmap Scanner with predefined scan profiles and Snipe-IT integration"""
    
    def __init__(self, network_ranges: Optional[List[str]] = None):
        if network_ranges is None:
            self.network_ranges = NMAP_SCAN_RANGES
        else:
            self.network_ranges = network_ranges
        self.nm = nmap.PortScanner()
        self.snipe_cache_clearer = SnipeCacheClearer()
    
    def run_scan(self, profile: str = 'discovery', targets: Optional[List[str]] = None) -> List[Dict]:
        """Run Nmap scan with specified profile"""
        
        if profile not in NMAP_SCAN_PROFILES:
            print(f"Unknown profile: {profile}")
            return []
        
        scan_config = NMAP_SCAN_PROFILES[profile]
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
        
        self.snipe_cache_clearer.clear_all_caches
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

    # Determine command and handle elevation
    command = sys.argv[1] if len(sys.argv) > 1 else 'discovery'
    is_categorization_debug = os.getenv('NMAP_CATEGORIZATION_DEBUG', '0') == '1'

    # Only elevate if we are running a valid scan profile.
    # This prevents sudo prompts for 'list', '--help', or typos.
    if not is_categorization_debug and command in NMAP_SCAN_PROFILES:
        elevate_to_root()

    debug_logger.clear_logs('nmap')
    
    scanner = NmapScanner()
    
    if command in NMAP_SCAN_PROFILES:
        scanner.scan_network(command)
    elif command == 'list':
        print("\nAvailable scan profiles:")
        for name, config in NMAP_SCAN_PROFILES.items():
            print(f"  {name:12} - {config['description']}")
    else:
        print(f"Unknown command: {command}")
        print("Usage: nmap_scanner.py [profile_name|list]")

if __name__ == "__main__":
    main()