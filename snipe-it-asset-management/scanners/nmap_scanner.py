"""Nmap scanner integration"""

import subprocess
import hashlib
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict
from ..lib.asset_matcher import AssetMatcher

class NmapScanner:
    """Nmap network scanner integration"""
    
    def __init__(self, network_range: str = "192.168.1.0/24"):
        self.network_range = network_range
        self.asset_matcher = AssetMatcher()
    
    def run_discovery_scan(self) -> List[Dict]:
        """Run basic discovery scan"""
        cmd = [
            'nmap', '-sn', '-PE', '-PA21,22,25,80,443,3389',
            '-PS21,22,25,80,443,3389', '-PU161',
            '--max-retries', '2', '--host-timeout', '30s',
            '-oX', '-', self.network_range
        ]
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return self._parse_nmap_xml(result.stdout)
        except Exception as e:
            print(f"Nmap scan failed: {e}")
            return []
    
    def run_intrusive_scan(self, targets: List[str]) -> List[Dict]:
        """Run detailed intrusive scan on specific targets"""
        assets = []
        
        for target in targets:
            cmd = [
                'nmap', '-A', '-sV', '-sC', '-O',
                '--script', 'vuln',
                '-oX', '-', target
            ]
            
            try:
                result = subprocess.run(cmd, capture_output=True, text=True)
                assets.extend(self._parse_nmap_xml(result.stdout, detailed=True))
            except Exception as e:
                print(f"Intrusive scan failed for {target}: {e}")
        
        return assets
    
    def _parse_nmap_xml(self, xml_output: str, detailed: bool = False) -> List[Dict]:
        """Parse Nmap XML output"""
        assets = []
        
        try:
            root = ET.fromstring(xml_output)
            
            for host in root.findall('.//host'):
                if host.find('.//status').get('state') != 'up':
                    continue
                
                asset = {
                    'first_seen_date': datetime.utcnow().isoformat(),
                    'nmap_last_scan': datetime.utcnow().isoformat(),
                    'device_type': 'Network Device'  # Will be refined
                }
                
                # Get IP address
                for address in host.findall('.//address'):
                    if address.get('addrtype') == 'ipv4':
                        asset['last_seen_ip'] = address.get('addr')
                    elif address.get('addrtype') == 'mac':
                        asset['mac_addresses'] = address.get('addr')
                
                # Get hostname
                for hostname in host.findall('.//hostname'):
                    asset['dns_hostname'] = hostname.get('name')
                    asset['name'] = hostname.get('name')
                
                if detailed:
                    # Get OS information
                    for osmatch in host.findall('.//osmatch'):
                        asset['nmap_os_guess'] = osmatch.get('name')
                        break
                    
                    # Get open ports
                    ports = []
                    for port in host.findall('.//port'):
                        if port.find('.//state').get('state') == 'open':
                            port_num = port.get('portid')
                            service = port.find('.//service')
                            if service is not None:
                                service_name = service.get('name', '')
                                ports.append(f"{port_num}/{service_name}")
                            else:
                                ports.append(port_num)
                    
                    if ports:
                        asset['nmap_open_ports'] = '\n'.join(ports)
                        asset['open_ports_hash'] = hashlib.md5(
                            ','.join(sorted(ports)).encode()
                        ).hexdigest()
                
                assets.append(asset)
        
        except Exception as e:
            print(f"Failed to parse Nmap XML: {e}")
        
        return assets
    
    def sync_to_snipeit(self) -> Dict:
        """Run scan and sync results to Snipe-IT"""
        print("Starting Nmap discovery scan...")
        discovered_assets = self.run_discovery_scan()
        
        print(f"Discovered {len(discovered_assets)} active hosts")
        
        # Process and sync to Snipe-IT
        results = self.asset_matcher.process_scan_data('nmap', discovered_assets)
        
        print(f"Sync complete: {results['created']} created, {results['updated']} updated")
        return results