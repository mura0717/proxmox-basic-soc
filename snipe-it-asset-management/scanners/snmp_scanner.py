#!/usr/bin/env python3
"""
SNMP Scanner for network device discovery
"""

import os
import sys
import argparse
from datetime import datetime, timezone
from typing import List, Dict, Optional
import ipaddress
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lib.asset_matcher import AssetMatcher
from pysnmp.hlapi import (
    getCmd,
    SnmpEngine,
    CommunityData,
    UdpTransportTarget,
    ContextData,
    ObjectType,
    ObjectIdentity
)

class SNMPScanner:
    """SNMP network device scanner"""
    
    def __init__(self, community: str = 'public'):
        self.community = community
        self.asset_matcher = AssetMatcher()
        self.timeout = 5
        self.retries = 2
        
        # Standard SNMP OIDs
        self.standard_oids = {
            'sysDescr': '1.3.6.1.2.1.1.1.0',
            'sysObjectID': '1.3.6.1.2.1.1.2.0',
            'sysUpTime': '1.3.6.1.2.1.1.3.0',
            'sysContact': '1.3.6.1.2.1.1.4.0',
            'sysName': '1.3.6.1.2.1.1.5.0',
            'sysLocation': '1.3.6.1.2.1.1.6.0',
            'ifNumber': '1.3.6.1.2.1.2.1.0',  # Number of interfaces
            'sysSerial': '1.3.6.1.2.1.47.1.1.1.1.11.1',  # ENTITY-MIB serial
            'ifPhysAddress.1': '1.3.6.1.2.1.2.2.1.6.1',  # First interface MAC
        }
        
        self.vendor_oids = {
            'cisco': {
                'serial': '1.3.6.1.2.1.47.1.1.1.1.11.1',
                'model': '1.3.6.1.2.1.47.1.1.1.1.13.1',
            },
            'hp': {
                'serial': '1.3.6.1.4.1.11.2.36.1.1.2.9.0',
                'model': '1.3.6.1.4.1.11.2.36.1.1.5.1.1.2.1',
            },
            'dell': {
                'service_tag': '1.3.6.1.4.1.674.10892.1.300.10.1.11.1',
            },
        }
            
    
    def scan_device(self, ip_address: str) -> Optional[Dict]:
        """Scan single device via SNMP"""
        
        current_time = datetime.now(timezone.utc).isoformat()
        device_info = {
            'last_seen_ip': ip_address,
            'device_type': 'Network Device',
            'last_update_source': 'snmp',
            'last_update_at': current_time,
            # Device identification
            'device_type': 'Network Device',
            'dns_hostname': None,
            'manufacturer': None,
            'model': None,
            
            # SNMP-specific data
            'snmp_sys_description': None,
            'snmp_location': None,
            'snmp_contact': None,
            'snmp_uptime': None,
            'switch_port_count': None,
            'mac_addresses': None,
            'notes': None,
        }
        
        found_snmp_data = False # Flag to check if any SNMP data was retrieved
        
        snmp_data = {}
        for oid_name, oid_value in self.standard_oids.items():
            try:
                result = self._snmp_get(ip_address, oid_value)
                if result:
                    found_snmp_data = True
                    snmp_data[oid_name] = result
            except Exception as e:
                print(f"SNMP error for {ip_address} OID {oid_name}: {e}")
        
        # Get MAC addresses from ARP table if it's a switch/router
        if 'switch' in device_info.get('device_type', '').lower():
            mac_addresses = self._get_mac_addresses(ip_address)
            if mac_addresses:
                device_info['mac_addresses'] = '\n'.join(mac_addresses)
        
        return device_info if found_snmp_data else None
    
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
        except(ValueError, TypeError):
            return timeticks
    
    def _get_mac_addresses(self, ip: str) -> List[str]:
        """Get MAC addresses from device (for switches)"""
        mac_addresses = []
        # Implementation depends on device vendor
        # This is a simplified example
        return mac_addresses
    
    def scan_network(self, network_range: str = "192.168.1.0/24") -> List[Dict]:
        """Scan network range for SNMP-enabled devices"""
        
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