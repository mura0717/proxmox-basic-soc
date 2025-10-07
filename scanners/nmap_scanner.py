#!/usr/bin/env python3
"""
Nmap scanner with integrated sudo handling
"""
import os
import sys
import subprocess

NO_ROOT_COMMANDS = ['discovery', 'web', 'list', 'help']

# Auto-elevate to root if needed
if len(sys.argv) > 1 and sys.argv[1] not in NO_ROOT_COMMANDS:
    if os.geteuid() != 0:
        print("Elevating to root privileges...")
        subprocess.call(['sudo', sys.executable] + sys.argv)
        sys.exit()

# Ensure parent directory is in sys.path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import nmap
import hashlib
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from lib.asset_matcher import AssetMatcher
from debug.asset_debug_logger import debug_logger

class NmapScanner:
    """Nmap Scanner with predefined scan profiles and Snipe-IT integration"""    
    SCAN_PROFILES = {
    # LEVEL 1: Discovery (No root, fastest)
    'discovery': {
        'args': '-sn -T4',
        'description': 'Fast ping sweep - finds live hosts',
        'frequency': 'hourly',
        'timeout': 300  # 5 minutes
    },
    
    # LEVEL 2: Quick Check (Basic ports)
    'quick': {
        'args': '-sS --top-ports 100 -T5 --open',
        'description': 'Quick port check - top 100 ports only',
        'frequency': 'daily',
        'timeout': 600  # 10 minutes
    },
    
    # LEVEL 3: Basic Inventory (Standard scan)
    'cybersec-inventory': {
        'args': '-sn -sS --top-ports 50 -T5 --open',  # Fast but gets some service info
        'description': 'Cybersecurity inventory - fast scan with basic service detection',
        'frequency': 'hourly',
        'timeout': 900  # 15 minutes
    },
    
    'basic': {
        'args': '-sS -sV --top-ports 1000 -T4',
        'description': 'Basic service detection - top 1000 ports',
        'frequency': 'daily_offhours',
        'timeout': 1800  # 30 minutes
    },
    
    # LEVEL 4: Detailed Inventory (With OS detection)
    'detailed': {
        'args': '-sS -sV -O --osscan-guess --top-ports 1000 -T4',
        'description': 'Service + OS detection',
        'frequency': 'weekly',
        'timeout': 3600  # 1 hour
    },
    
    # LEVEL 5: Vulnerability Scan
    'vulnerability': {
        'args': '-sS -sV --script vuln,exploit -T3',
        'description': 'Security vulnerability detection',
        'frequency': 'weekly_weekend',
        'timeout': 7200  # 2 hours
    },
    
    # LEVEL 6: Full Audit (Comprehensive)
    'full': {
        'args': '-sS -sV -O -A --script default,discovery -p- -T4',
        'description': 'Complete port and service audit - ALL ports',
        'frequency': 'monthly',
        'timeout': 14400  # 4 hours
    },
    
    # SPECIAL: Web Applications
    'web': {
        'args': '-sV -p80,443,8080,8443 --script http-enum,http-title',
        'description': 'Web application discovery',
        'frequency': 'daily',
        'timeout': 900  # 15 minutes
    },
    
    # SPECIAL: Network Devices (SNMP/SSH)
    'network': {
        'args': '-sU -sS -p161,22,23 --script snmp-info',
        'description': 'Network device identification',
        'frequency': 'daily',
        'timeout': 1200  # 20 minutes
    }
}
    
    def __init__(self, network_range: str = "192.168.1.0/24"):
        self.network_range = network_range
        self.nm = nmap.PortScanner()
        self.asset_matcher = AssetMatcher()
    
    def run_scan(self, profile: str = 'discovery', targets: Optional[List[str]] = None) -> List[Dict]:
        """Run Nmap scan with specified profile"""
        
        if profile not in self.SCAN_PROFILES:
            print(f"Unknown profile: {profile}")
            return []
        
        scan_config = self.SCAN_PROFILES[profile]
        scan_targets = ' '.join(targets) if targets else self.network_range
        
        print(f"Running {profile} scan: {scan_config['description']}")
        print(f"Targets: {scan_targets}")
        
        try:
            # Run the scan
            self.nm.scan(hosts=scan_targets, arguments=scan_config['args'])
            
            # Parse results
            assets = []
            for host in self.nm.all_hosts():
                if self.nm[host].state() == 'up':
                    asset = self._parse_host(host, profile)
                    assets.append(asset)
            
            return assets
            
        except nmap.PortScannerError as e:
            print(f"Nmap error: {e}")
            return []
        except Exception as e:
            print(f"Scan failed: {e}")
            return []
    
    def _parse_host(self, host: str, profile: str) -> Dict:
        """
        Parse single host results - DATA COLLECTION ONLY.
        This method's only job is to extract raw data from Nmap.
        All categorization logic is handled by the AssetMatcher/AssetCategorizer.
        """
        nmap_host = self.nm[host]

        # This dictionary holds all the raw data we can find.
        asset = {
            'last_seen_ip': host,
            'nmap_last_scan': datetime.now(timezone.utc).isoformat(),
            'nmap_scan_profile': profile,
            'name': nmap_host.hostname() or f"Device-{host}",
            'dns_hostname': nmap_host.hostname(),
            '_source': 'nmap',
            # We will populate these fields if the data exists.
            'mac_addresses': None,
            'manufacturer': None,
            'os_platform': None,
            'nmap_os_guess': None,
            'os_accuracy': None,
            'nmap_open_ports': None,
            'open_ports_hash': None,
            'nmap_services': [],
        }

        # Get MAC and Manufacturer from MAC Vendor
        if 'mac' in nmap_host.get('addresses', {}):
            asset['mac_addresses'] = nmap_host['addresses']['mac']
            if 'vendor' in nmap_host and nmap_host['vendor']:
                asset['manufacturer'] = list(nmap_host['vendor'].values())[0]

        # Get OS Guess (take the first, most accurate match)
        if profile != 'discovery' and 'osmatch' in nmap_host and nmap_host['osmatch']:
            os_match = nmap_host['osmatch'][0]
            asset['nmap_os_guess'] = os_match.get('name', '')
            asset['os_accuracy'] = os_match.get('accuracy')
            asset['os_platform'] = os_match.get('name', '') # Crucial for the categorizer

        # Get Port and Service Information
        if profile != 'discovery':
            open_ports_list = []
            service_names = []
            
            for proto in nmap_host.all_protocols():
                for port, port_info in nmap_host[proto].items():
                    if port_info.get('state') == 'open':
                        service_name = port_info.get('name', 'unknown')
                        service_names.append(service_name)
                        
                        # Build the descriptive port string for storage
                        product = port_info.get('product', '')
                        version = port_info.get('version', '')
                        port_str = f"{port}/{proto}/{service_name} ({product} {version})".strip()
                        open_ports_list.append(port_str)
            
            if open_ports_list:
                asset['nmap_open_ports'] = '\n'.join(sorted(open_ports_list))
                asset['open_ports_hash'] = hashlib.md5(asset['nmap_open_ports'].encode()).hexdigest()
                asset['nmap_services'] = service_names

        # Set first seen timestamp
        asset['first_seen_date'] = datetime.now(timezone.utc).isoformat()
        
        # Return a clean dictionary with no None values
        return {k: v for k, v in asset.items() if v is not None and v != '' and v != []}
    
    def sync_to_snipeit(self, profile: str = 'discovery') -> Dict:
        """Run scan and sync to Snipe-IT"""
        print(f"Starting {profile} scan...")
        
        if debug_logger.nmap_debug:
            debug_logger._clear_all_debug_logs()
            debug_logger._debug_log(
                f"=== NMAP SCAN SESSION STARTED ===\nProfile: {profile}\nNetwork: {self.network_range}\n",
                debug_logger.raw_nmap_log_file
        )
        
        assets = self.run_scan(profile)
        
        if not assets:
            if debug_logger.nmap_debug:
                debug_logger._debug_log("No assets discovered in scan", debug_logger.raw_nmap_log_file)
            return {'created': 0, 'updated': 0, 'failed': 0}
        
        print(f"Found {len(assets)} hosts")
        
        if debug_logger.nmap_debug:
            for asset in assets:
                debug_logger._nmap_raw_data_log(
                    f"\n--- ASSET TO SYNC: {asset.get('name')} ---\n{json.dumps(asset, indent=2)}\n{'-'*50}\n"
                )
        
        results = self.asset_matcher.process_scan_data('nmap', assets)
        
        if debug_logger.nmap_debug:
            for result in results:
                debug_logger._nmap_transformed_data_log(
                    f"\n=== SYNC RESULTS ===\nCreated: {result['created']}\nUpdated: {result['updated']}\nFailed: {result['failed']}\n{'='*50}\n"
                    )
        
        print(f"Sync complete: {results['created']} created, {results['updated']} updated")
        return results

def main():
    """Command-line interface"""
    import sys
    
    scanner = NmapScanner()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command in scanner.SCAN_PROFILES:
            scanner.sync_to_snipeit(command)
        elif command == 'list':
            print("\nAvailable scan profiles:")
            for name, config in scanner.SCAN_PROFILES.items():
                print(f"  {name:12} - {config['description']}")
        else:
            print(f"Unknown command: {command}")
            print("Usage: nmap_scanner.py [discovery|quick|cybcersec_inventory|basic|detailed|vulnerability|full|web|network|list]")
    else:
        scanner.sync_to_snipeit('discovery')

if __name__ == "__main__":
    main()