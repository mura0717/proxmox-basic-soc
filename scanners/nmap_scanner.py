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
from datetime import datetime, timezone
from typing import List, Dict, Optional
from lib.asset_matcher import AssetMatcher

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
        """Parse single host results"""
        
        asset = {
            'last_seen_ip': host,
            'nmap_last_scan': datetime.now(timezone.utc).isoformat(),
            'nmap_scan_profile': profile,
            'device_type': 'Unknown'
        }
        
        # Get hostname
        if self.nm[host].hostname():
            asset['dns_hostname'] = self.nm[host].hostname()
            asset['name'] = self.nm[host].hostname()
        else:
            asset['name'] = f"Device-{host}"
        
        # Get MAC address
        if 'mac' in self.nm[host]['addresses']:
            asset['mac_addresses'] = self.nm[host]['addresses']['mac']
            
            # Get vendor if available
            if 'vendor' in self.nm[host] and self.nm[host]['vendor']:
                vendors = list(self.nm[host]['vendor'].values())
                if vendors:
                    asset['manufacturer'] = vendors[0]
        
        # OS detection (for non-discovery scans)
        if profile != 'discovery' and 'osmatch' in self.nm[host]:
            for osmatch in self.nm[host]['osmatch']:
                asset['nmap_os_guess'] = osmatch['name']
                asset['os_accuracy'] = osmatch['accuracy']
                asset['device_type'] = self._determine_device_type(osmatch['name'])
                break
        
        # Port information
        if profile != 'discovery':
            ports = []
            services = []
            
            for proto in self.nm[host].all_protocols():
                for port in self.nm[host][proto].keys():
                    port_info = self.nm[host][proto][port]
                    if port_info['state'] == 'open':
                        service = port_info.get('name', 'unknown')
                        product = port_info.get('product', '')
                        version = port_info.get('version', '')
                        
                        port_str = f"{port}/{proto}/{service}"
                        if product:
                            port_str += f" ({product}"
                            if version:
                                port_str += f" {version}"
                            port_str += ")"
                        
                        ports.append(port_str)
                        services.append(service)
            
            if ports:
                asset['nmap_open_ports'] = '\n'.join(ports)
                asset['open_ports_hash'] = hashlib.md5(
                    ','.join(sorted(ports)).encode()
                ).hexdigest()
                
                # Refine device type based on services
                if services:
                    asset['device_type'] = self._refine_device_type_by_services(
                        asset.get('device_type', 'Unknown'),
                        services
                    )
        
        # Set first seen if new
        if not asset.get('first_seen_date'):
            asset['first_seen_date'] = datetime.now(timezone.utc).isoformat()
        
        return asset
    
    def _determine_device_type(self, os_string: str) -> str:
        """Determine device type from OS string"""
        os_lower = os_string.lower()
        
        if any(x in os_lower for x in ['cisco', 'switch', 'catalyst']):
            return 'Switch'
        elif any(x in os_lower for x in ['router', 'mikrotik']):
            return 'Router'
        elif any(x in os_lower for x in ['firewall', 'fortigate', 'pfsense']):
            return 'Firewall'
        elif 'windows server' in os_lower:
            return 'Server'
        elif 'windows' in os_lower:
            return 'Desktop'
        elif 'linux' in os_lower:
            return 'Linux Device'
        elif any(x in os_lower for x in ['printer', 'jetdirect']):
            return 'Printer'
        else:
            return 'Network Device'
    
    def _refine_device_type_by_services(self, current_type: str, services: List[str]) -> str:
        """Refine device type based on services"""
        service_str = ' '.join(services).lower()
        
        if 'domain' in service_str and 'ldap' in service_str:
            return 'Domain Controller'
        elif 'http' in service_str and 'printer' in service_str:
            return 'Printer'
        elif any(db in service_str for db in ['mysql', 'mssql', 'postgresql']):
            return 'Database Server'
        
        return current_type
    
    def sync_to_snipeit(self, profile: str = 'discovery') -> Dict:
        """Run scan and sync to Snipe-IT"""
        print(f"Starting {profile} scan...")
        assets = self.run_scan(profile)
        
        if not assets:
            return {'created': 0, 'updated': 0, 'failed': 0}
        
        print(f"Found {len(assets)} hosts")
        results = self.asset_matcher.process_scan_data('nmap', assets)
        
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
            print("Usage: nmap_scanner.py [discovery|quick|basic|detailed|vulnerability|full|web|network|list]")
    else:
        scanner.sync_to_snipeit('discovery')

if __name__ == "__main__":
    main()