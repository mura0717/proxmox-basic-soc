import os
import sys
from typing import Dict, List, Optional
from ipaddress import ip_address, AddressValueError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from debug.asset_debug_logger import debug_logger
from config import categorization_rules
from assets_sync_library.text_utils import normalize_for_comparison
from config import network_config

class AssetCategorizer:
    """Determines device type and category based on attributes."""
    def __init__(self):
        pass
    
    @classmethod
    def _is_static_ip(cls, ip_address: str) -> bool:
        """Check if an IP is in our static mapping"""
        return ip_address in network_config.STATIC_IP_MAP

    @classmethod
    def _categorize_by_static_ip(cls, ip_address: Optional[str]) -> Optional[Dict]:
        """Looks up a device in the hardcoded static IP map."""
        if not ip_address:
            return None
        return network_config.STATIC_IP_MAP.get(ip_address)

    @classmethod
    def _categorize_network_device(cls, model: str, manufacturer: str, device_name: str) -> str | None:
        """Categorizes network devices using a structured rule set."""
        device_type_priority = ['Firewall', 'Switch', 'Router', 'Access Point']

        for device_type in device_type_priority:
            rule_set = categorization_rules.NETWORK_DEVICE_RULES.get(device_type, {})
            
            # Special check for Access Points by hostname prefix
            if device_type == 'Access Point' and device_name.lower().startswith('ap'):
                return 'Access Point'
            
            if any(vendor in manufacturer for vendor in rule_set.get('vendors', [])) and \
               (not rule_set.get('model_keywords') or not model or \
                any(keyword in model for keyword in rule_set.get('model_keywords', []))):
                    return device_type
        return None
    
    @classmethod
    def _categorize_by_services(cls, services: List[str]) -> str | None:
        """Determine device type based on a list of open services."""
        if not services:
            return None
        
        service_str = ' '.join(services).lower()
        
        if 'domain' in service_str and 'ldap' in service_str:
            return 'Domain Controller'
        if any(svc in service_str for svc in ['ipp', 'jetdirect', 'printer', 'cups']):
            return 'Printer'
        if any(db in service_str for db in ['mysql', 'mssql', 'postgresql', 'oracle', 'mongodb']):
            return 'Database Server'
        if any(svc in service_str for svc in ['nfs', 'smb', 'cifs', 'iscsi']):
            return 'Storage Device'
        if ('http' in service_str or 'https' in service_str):
            return 'Web Server'
        if 'snmp' in service_str:
            return 'Network Device' # Generic fallback if SNMP is seen
        return None
    
    @classmethod
    def _categorize_vm(cls, manufacturer: str, model: str) -> Optional[str]:
        """Categorize a device as a Virtual Machine."""
        if any(vendor in manufacturer for vendor in categorization_rules.VIRTUAL_MACHINE_RULES['vendors']) and \
           any(kw in model for kw in categorization_rules.VIRTUAL_MACHINE_RULES['model_keywords']):
            return 'Virtual Machine'
        return None

    @classmethod
    def _categorize_server(cls, os_type: str, model: str, device_name: str) -> Optional[str]:
        """Categorize a device as a Server."""
        if any(kw in os_type for kw in categorization_rules.SERVER_RULES['os_keywords']) or \
           any(kw in model for kw in categorization_rules.SERVER_RULES['model_keywords']) or \
           any(kw in device_name for kw in categorization_rules.SERVER_RULES.get('hostname_keywords', [])):
            return 'Server'
        return None

    @classmethod
    def _categorize_ios(cls, os_type: str, model: str, device_name: str) -> Optional[str]:
        """Categorize an iOS device as a Tablet or Mobile Phone."""
        if 'ios' not in os_type:
            return None
        if any(kw in model or kw in device_name for kw in categorization_rules.IOS_RULES['tablet_keywords']):
            return 'Tablet'
        return 'Mobile Phone'

    @classmethod
    def _categorize_android(cls, os_type: str, model: str, manufacturer: str) -> Optional[str]:
        """Categorize an Android device as a Tablet, IoT, or Mobile Phone."""
        if 'android' not in os_type:
            return None
            
        if any(kw in model for kw in categorization_rules.ANDROID_RULES['iot_keywords']):
            return 'IoT Devices'
        if any(kw in model for kw in categorization_rules.ANDROID_RULES['tablet_keywords']) or \
           any(vendor in manufacturer for vendor in categorization_rules.ANDROID_RULES['tablet_vendors']):
            return 'Tablet'
        return 'Mobile Phone'

    @classmethod
    def _categorize_computer(cls, os_type: str, model: str, manufacturer: str, device_name: str) -> Optional[str]:
        """Categorize a computer as a Laptop or Desktop."""
        if 'windows' not in os_type and 'mac' not in os_type:
            return None

        # Check for Laptop
        if any(marker in model for marker in categorization_rules.COMPUTER_RULES['laptop_keywords']):
            return 'Laptop'
        if manufacturer in categorization_rules.COMPUTER_RULES['laptop_vendor_prefixes'] and \
           any(model.startswith(p) for p in categorization_rules.COMPUTER_RULES['laptop_vendor_prefixes'][manufacturer]):
            return 'Laptop'
        if any(kw in device_name for kw in categorization_rules.COMPUTER_RULES['laptop_hostname_keywords']):
            return 'Laptop'

        # Check for Desktop
        if any(marker in model for marker in categorization_rules.COMPUTER_RULES['desktop_keywords']):
            return 'Desktop'
        if manufacturer in categorization_rules.COMPUTER_RULES['desktop_vendor_prefixes'] and \
           any(model.startswith(p) for p in categorization_rules.COMPUTER_RULES['desktop_vendor_prefixes'][manufacturer]):
            return 'Desktop'
        if any(kw in device_name for kw in categorization_rules.COMPUTER_RULES['desktop_hostname_keywords']):
            return 'Desktop'
        if any(kw in os_type for kw in categorization_rules.COMPUTER_RULES['desktop_os_keywords']):
            return 'Desktop'
            
        return 'Desktop' # Default for a computer if not explicitly a laptop

    @classmethod
    def _categorize_generic_os_device(cls, os_type: str, model: str) -> Optional[str]:
        """Categorize a device based on generic OS and inferred model."""
        if 'windows server' in model or 'linux server' in model:
            return 'Server'
        if 'windows workstation' in model or 'linux workstation' in model or 'macos device' in model:
            return 'Desktop'
        if 'windows' in os_type or 'mac' in os_type or 'linux' in os_type:
            return 'Desktop'
        return None

    @classmethod
    def _categorize_iot(cls, model: str, os_type: str, device_name: str) -> Optional[str]:
        """Categorize a device as IoT."""
        clean_device_name = normalize_for_comparison(device_name)
               
        if any(kw in model for kw in categorization_rules.IOT_RULES['model_keywords']) or \
           any(kw in os_type for kw in categorization_rules.IOT_RULES['os_keywords']) or \
           any(kw in clean_device_name for kw in categorization_rules.IOT_RULES.get('hostname_keywords', [])):
               
            return 'IoT Devices'
        return None

    @classmethod
    def _determine_cloud_provider(self, intune_device: Dict) -> str | None: 
        """ Determines the cloud provider based on device manufacturer and model. """ 
        raw_manufacturer = intune_device.get('manufacturer') or ''
        if isinstance(raw_manufacturer, dict):
            raw_manufacturer = raw_manufacturer.get('name', '') or ''
        manufacturer = raw_manufacturer.lower()
    
    # Handle model field - can be dict or string
        raw_model = intune_device.get('model') or ''
        if isinstance(raw_model, dict):
            raw_model = raw_model.get('name', '') or raw_model.get('model_number', '') or ''
        model = raw_model.lower()
        if 'yealink' in manufacturer:
            return None
        if 'microsoft corporation' in manufacturer and 'virtual machine' in model: 
            return 'Azure'
        if 'amazon' in manufacturer or 'aws' in manufacturer or 'amazon ec2' in model: 
            return 'AWS'
        return 'On-Premise'
    
    @classmethod
    def _get_location_from_dhcp_scope(cls, ip: Optional[str]) -> Optional[Dict]:
        """
        Determines the location of a device by checking if its IP falls within a DHCP scope.
        Returns the entire scope dictionary if a match is found.
        """
        if not ip:
            return None

        try:
            target_addr = ip_address(ip)
            for scope in network_config.DHCP_SCOPES:
                start_addr = ip_address(scope['start_ip'])
                end_addr = ip_address(scope['end_ip'])
                if start_addr <= target_addr <= end_addr:
                    return scope
        except (AddressValueError, KeyError):
            # Handles invalid IP strings or malformed scope dictionaries
            return None
        return None
    
    @classmethod
    def categorize(cls, device_data: Dict) -> Dict[str, str]:
        """Compute device_type and category from data."""
        
        # --- 1. Initialization and Data Extraction ---
        source = device_data.get('_source', 'unknown')
        ip_address = device_data.get('last_seen_ip')
        
        # Initialize services from the discovered data
        nmap_services = device_data.get('nmap_services', [])
        
        # --- 2. Static IP Mapping Override (Highest Priority) ---
        static_info = None
        if ip_address and cls._is_static_ip(ip_address):
            static_info = cls._categorize_by_static_ip(ip_address)
            
        if static_info:
            # If a static entry is found, merge its data into the device data
            device_data.update(static_info)
            static_services_str = static_info.get('services', '')

            # If the static map provides a 'services' string, parse it into the list of services for categorization.
            if static_services_str:
                static_services_list = [s.strip() for s in static_services_str.split(',')]
                nmap_services = list(dict.fromkeys(static_services_list + nmap_services))
        
        # --- 3. DHCP Scope Location Fallback (Medium Priority) ---        
        if 'location' not in device_data:
            dhcp_info = cls._get_location_from_dhcp_scope(ip_address)
            if dhcp_info and dhcp_info.get('location'):
                device_data['location'] = dhcp_info['location']
        
        # --- 4. Normalize Data for Comparison Logic ---    
        # Raw for Debug only
        raw_name = (device_data.get('name') or device_data.get('deviceName') or '')
        raw_os = (device_data.get('os_platform') or device_data.get('operatingSystem') or '')
        
        raw_model = device_data.get('model') or ''
        if isinstance(raw_model, dict):
        # Extract name from Snipe-IT model object
            raw_model = raw_model.get('name', '') or raw_model.get('model_number', '') or ''
        
        raw_mfr = device_data.get('manufacturer') or ''
        if isinstance(raw_mfr, dict):
            # Extract name from Snipe-IT manufacturer object
            raw_mfr = raw_mfr.get('name', '') or ''
        
        raw_serial = (device_data.get('serial') or '') # Only for debugging - for easier search in logs
        
        # Normalized for Comparison Logic
        device_name = raw_name.lower()
        os_type = raw_os.lower()
        model = raw_model.lower()
        manufacturer = raw_mfr.lower()
        cloud_provider = cls._determine_cloud_provider(device_data)
        
        # -------------DEBUG---------------
        """Device data log for debugging"""
        log_entry = (
            f"--- Device: {raw_name or 'Unknown'} ---\n"
            f"  Serial:       {raw_serial}\n"
            f"  OS Type:      {raw_os}\n"
            f"  Model:        {raw_model}\n"
            f"  Manufacturer: {raw_mfr}\n"
            f"  Nmap Services:     {', '.join(nmap_services) if nmap_services else 'None'}\n"
            f"  Cloud Provider: {cloud_provider}\n"
            f"{'-'*50}\n"
        )
        debug_logger.log_categorization(source, log_entry)
        
        # --- 5. Categorization Priority Chain ---
        device_type = device_data.get('device_type')
        if not device_type:
            device_type = (
                # --- Hardware-based Categorization (Highest Priority) ---
                # 1. Virtual Machines (very specific)
                cls._categorize_vm(manufacturer, model) or
                
                # 2. IoT Devices (Yealink, etc. - check before general Android)
                cls._categorize_iot(model, os_type, device_name) or
                
                # 3. Network Infrastructure (Switches, Routers, etc.)
                cls._categorize_network_device(model, manufacturer, device_name) or
                
                # 4. Mobile Devices (iOS/Android Phones/Tablets)
                cls._categorize_ios(os_type, model, device_name) or
                cls._categorize_android(os_type, model, manufacturer) or
                
                # 5. Computers (Laptops/Desktops)
                cls._categorize_computer(os_type, model, manufacturer, device_name) or
                
                # --- OS & Service-based Categorization (Lower Priority) ---
                # 6. Servers (based on OS name)
                cls._categorize_server(os_type, model, device_name) or
                
                # 7. By specific services (e.g., Printer, Domain Controller)
                cls._categorize_by_services(nmap_services) or
                
                # 8. Generic OS-based devices (e.g., Windows Workstation, Linux Server)
                cls._categorize_generic_os_device(os_type, model) or
                
                # 9. Default fallback
                'Other Device'
            )

        # --- 6. Category Mapping ---
        # Use the category from the static map if available, otherwise map the device type.
        category = device_data.get('category') or categorization_rules.CATEGORY_MAP.get(device_type, 'Other Assets')
        if cloud_provider in ['Azure', 'AWS', 'GCP']:
            category = 'Cloud Resources'

        return {'device_type': device_type, 'category': category, 'cloud_provider': cloud_provider}