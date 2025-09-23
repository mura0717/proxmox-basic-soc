#!/usr/bin/env python3
"""
SNMP Scanner for network device discovery
"""

import os
from datetime import datetime, timezone
from typing import List, Dict, Optional
from pysnmp.hlapi import (
    getCmd,
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity
)
from ..lib.asset_matcher import AssetMatcher

class SNMPScanner:
    """SNMP network device scanner"""
    
    def __init__(self, community: str = 'public'):
        self.community = community
        self.asset_matcher = AssetMatcher()
        self.timeout = 5
        self.retries = 2
        
        # Standard SNMP OIDs
        self.oids = {
            'sysDescr': '1.3.6.1.2.1.1.1.0',
            'sysObjectID': '1.3.6.1.2.1.1.2.0',
            'sysUpTime': '1.3.6.1.2.1.1.3.0',
            'sysContact': '1.3.6.1.2.1.1.4.0',
            'sysName': '1.3.6.1.2.1.1.5.0',
            'sysLocation': '1.3.6.1.2.1.1.6.0',
            'ifNumber': '1.3.6.1.2.1.2.1.0',  # Number of interfaces
        }
    
    def scan_device(self, ip_address: str) -> Optional[Dict]:
        """Scan single device via SNMP"""
        device_info = {
            'last_seen_ip': ip_address,
            'device_type': 'Network Device',
            'last_update_source': 'snmp',
            'last_update_at': datetime.now(timezone.utc).isoformat()
        }
        
        for oid_name, oid_value in self.oids.items():
            try:
                result = self._snmp_get(ip_address, oid_value)
                if result:
                    if oid_name == 'sysName':
                        device_info['dns_hostname'] = result
                        device_info['name'] = result
                    elif oid_name == 'sysDescr':
                        device_info['notes'] = result
                        device_info['device_type'] = self._determine_device_type(result)
                    elif oid_name == 'sysLocation':
                        device_info['snmp_location'] = result
                    elif oid_name == 'sysContact':
                        device_info['snmp_contact'] = result
                    elif oid_name == 'sysUpTime':
                        device_info['snmp_uptime'] = self._format_uptime(result)
                    elif oid_name == 'ifNumber':
                        device_info['switch_port_count'] = result
            except Exception as e:
                print(f"SNMP error for {ip_address}: {e}")
        
        # Get MAC addresses from ARP table if it's a switch/router
        if 'switch' in device_info.get('device_type', '').lower():
            mac_addresses = self._get_mac_addresses(ip_address)
            if mac_addresses:
                device_info['mac_addresses'] = '\n'.join(mac_addresses)
        
        return device_info if len(device_info) > 3 else None
    
    def _snmp_get(self, ip: str, oid: str) -> Optional[str]:
        """Perform SNMP GET operation"""
        iterator = getCmd(
            SnmpEngine(),
            CommunityData(self.community),
            UdpTransportTarget((ip, 161), timeout=self.timeout, retries=self.retries),
            ContextData(),
            ObjectType(ObjectIdentity(oid))
        )
        
        errorIndication, errorStatus, errorIndex, varBinds = next(iterator)
        
        if errorIndication:
            return None
        elif errorStatus:
            return None
        else:
            for varBind in varBinds:
                return str(varBind[1])
        
        return None
    
    def _determine_device_type(self, sys_descr: str) -> str:
        """Determine device type from system description"""
        sys_descr_lower = sys_descr.lower()
        
        if 'switch' in sys_descr_lower:
            return 'Switch'
        elif 'router' in sys_descr_lower:
            return 'Router'
        elif 'firewall' in sys_descr_lower or 'asa' in sys_descr_lower:
            return 'Firewall'
        elif 'printer' in sys_descr_lower:
            return 'Printer'
        elif 'ups' in sys_descr_lower:
            return 'UPS'
        elif 'access point' in sys_descr_lower or 'ap' in sys_descr_lower:
            return 'Access Point'
        else:
            return 'Network Device'
    
    def _format_uptime(self, timeticks: str) -> str:
        """Convert SNMP timeticks to readable format"""
        try:
            ticks = int(timeticks)
            days = ticks // 8640000
            hours = (ticks % 8640000) // 360000
            minutes = (ticks % 360000) // 6000
            return f"{days}d {hours}h {minutes}m"
        except:
            return timeticks
    
    def _get_mac_addresses(self, ip: str) -> List[str]:
        """Get MAC addresses from device (for switches)"""
        mac_addresses = []
        # Implementation depends on device vendor
        # This is a simplified example
        return mac_addresses
    
    def scan_network(self, network_range: str = "192.168.1.0/24") -> List[Dict]:
        """Scan network range for SNMP-enabled devices"""
        import ipaddress
        
        devices = []
        network = ipaddress.ip_network(network_range)
        
        print(f"Scanning {network_range} for SNMP devices...")
        
        for ip in network.hosts():
            device = self.scan_device(str(ip))
            if device:
                devices.append(device)
                print(f"Found SNMP device: {device.get('name', ip)}")
        
        return devices
    
    def sync_to_snipeit(self, network_range: str = "192.168.1.0/24") -> Dict:
        """Scan and sync to Snipe-IT"""
        devices = self.scan_network(network_range)
        
        if not devices:
            print("No SNMP devices found")
            return {'created': 0, 'updated': 0, 'failed': 0}
        
        results = self.asset_matcher.process_scan_data('snmp', devices)
        print(f"SNMP sync complete: {results['created']} created, {results['updated']} updated")
        return results

if __name__ == "__main__":
    scanner = SNMPScanner(community=os.getenv('SNMP_COMMUNITY', 'public'))
    scanner.sync_to_snipeit()