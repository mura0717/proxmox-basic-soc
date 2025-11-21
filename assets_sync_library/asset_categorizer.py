import os
import sys
from typing import Dict, List, Optional
from ipaddress import ip_address, AddressValueError

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from debug.asset_debug_logger import debug_logger
from config import categorization_rules
from utils.text_utils import normalize_for_comparison
from config import network_config

class AssetCategorizer:
    """Determines asset device type and category based on a variety of data points."""
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
    def _normalize_hardware_identity(cls, manufacturer: str, model: str) -> tuple[str, str]:
        """
        Cleans up manufacturer data when a NIC vendor is mistakenly identified as the device manufacturer.
        """
        mfr_lower = manufacturer.lower()
        model_lower = model.lower()

        # First, check for complex cleanup rules
        for rule_mfr, rule_data in categorization_rules.MANUFACTURER_CLEANUP_RULES.items():
            if rule_mfr in mfr_lower:
                new_mfr = rule_data["target_manufacturer"]
                new_model = model.replace(rule_data["remove_from_model"], "").strip()
                return new_mfr, new_model

        # If the manufacturer is a known NIC vendor, try to find the real vendor in the model string.
        if any(nic in mfr_lower for nic in categorization_rules.NIC_VENDORS):
            if 'lenovo' in model_lower:
                return 'Lenovo', model
            if 'dell' in model_lower:
                return 'Dell', model
            if 'hp' in model_lower or 'hewlett' in model_lower:
                return 'HP', model
            # Fallback to prevent overwriting good data with a known-bad NIC vendor.
            return 'Generic', model
        
        return manufacturer, model
    
    @classmethod
    def _categorize_network_device(cls, model: str, manufacturer: str, device_name: str) -> str | None:
        """Categorizes network devices using a structured rule set."""
        priority_order = ['Firewall', 'Switch', 'Router', 'Access Point']
        clean_device_name = normalize_for_comparison(device_name)

        # Tier 1: Hostname Prefix Check (Highest Priority)
        for device_type in priority_order:
            rules = categorization_rules.NETWORK_DEVICE_RULES.get(device_type, {})
            if any(clean_device_name.startswith(prefix) for prefix in rules.get('hostname_prefixes', [])):
                return device_type

        # Tier 2: Vendor AND Model Check (Medium Priority)
        for device_type in priority_order:
            rules = categorization_rules.NETWORK_DEVICE_RULES.get(device_type, {})
            
            vendor_match = any(vendor in manufacturer for vendor in rules.get('vendors', []))
            if vendor_match and model and any(keyword in model for keyword in rules.get('model_keywords', [])):
                return device_type

        return None
    
    @classmethod
    def _categorize_by_services(cls, services: List[str]) -> str | None:
        """Determine device type based on a list of open services."""
        if not services:
            return None

        # Use the normalized string for more reliable matching
        service_str = normalize_for_comparison(' '.join(services))
        
        dc_keywords = categorization_rules.SERVICE_RULES['Domain Controller']['service_keywords']
        if all(kw in service_str for kw in dc_keywords):
            return 'Domain Controller'
        if any(svc in service_str for svc in categorization_rules.SERVICE_RULES['Printer']['service_keywords']):
            return 'Printer'
        if any(db in service_str for db in categorization_rules.SERVICE_RULES['Database Server']['service_keywords']):
            return 'Database Server'
        if any(svc in service_str for svc in categorization_rules.SERVICE_RULES['Storage Device']['service_keywords']):
            return 'Storage Device'
        if any(svc in service_str for svc in categorization_rules.SERVICE_RULES['Web Server']['service_keywords']):
            return 'Web Server'
        if any(svc in service_str for svc in categorization_rules.SERVICE_RULES['Network Device']['service_keywords']):
            return 'Network Device'
        return None
    
    @classmethod
    def _categorize_vm(cls, manufacturer: str, model: str, device_name: str) -> Optional[str]:
        """Categorize a device as a Virtual Machine."""
        if (any(vendor in manufacturer for vendor in categorization_rules.VIRTUAL_MACHINE_RULES['vendors']) and \
           any(kw in model for kw in categorization_rules.VIRTUAL_MACHINE_RULES['model_keywords'])) or \
           any(kw in device_name for kw in categorization_rules.VIRTUAL_MACHINE_RULES.get('hostname_keywords', [])):
            return 'Virtual Machine'
        return None

    @classmethod
    def _categorize_server(cls, os_type: str, model: str, device_name: str) -> Optional[str]:
        """Categorize a device as a Server."""
        if any(kw in os_type for kw in categorization_rules.SERVER_RULES['os_keywords']) or \
           any(kw in model for kw in categorization_rules.SERVER_RULES['model_keywords']):
            return 'Server'
        clean_name = normalize_for_comparison(device_name)
        if any(kw in clean_name for kw in categorization_rules.SERVER_RULES.get('hostname_keywords', [])):
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
            return 'IoT Device'
        if any(kw in model for kw in categorization_rules.ANDROID_RULES['tablet_keywords']) or \
           any(vendor in manufacturer for vendor in categorization_rules.ANDROID_RULES['tablet_vendors']):
            return 'Tablet'
        return 'Mobile Phone'

    @classmethod
    def _categorize_computer(cls, os_type: str, model: str, manufacturer: str, device_name: str) -> Optional[str]:
        """
        Categorize a computer as a Laptop or Desktop.
        PRIORITY: Hostname > Model > OS
        """
        # 1. Hostname Check (Highest Priority - Overrides bad Manufacturer data)
        if any(kw in device_name for kw in categorization_rules.COMPUTER_RULES['laptop_hostname_keywords']):
            return 'Laptop'
        if any(kw in device_name for kw in categorization_rules.COMPUTER_RULES['desktop_hostname_keywords']):
            return 'Desktop'

        # 2. Model Keyword Check
        if any(marker in model for marker in categorization_rules.COMPUTER_RULES['laptop_keywords']):
            return 'Laptop'
        if any(marker in model for marker in categorization_rules.COMPUTER_RULES['desktop_keywords']):
            return 'Desktop'

        # 3. OS Check 
        if 'windows' in os_type or 'mac' in os_type:
             if any(kw in os_type for kw in categorization_rules.COMPUTER_RULES['desktop_os_keywords']):
                return 'Desktop'
             # If it runs Windows but we can't determine form factor, default to Desktop
             return 'Desktop'

        return None

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
    def _categorize_iot(cls, model: str, manufacturer: str, os_type: str, device_name: str) -> Optional[str]:
        """Categorize a device as IoT."""
        clean_device_name = normalize_for_comparison(device_name)
        
        if any(kw in manufacturer for kw in categorization_rules.IOT_RULES.get('manufacturer_keywords', [])):
             return 'IoT Device'
               
        if any(kw in model for kw in categorization_rules.IOT_RULES['model_keywords']) or \
           any(kw in os_type for kw in categorization_rules.IOT_RULES['os_keywords']) or \
           any(kw in clean_device_name for kw in categorization_rules.IOT_RULES.get('hostname_keywords', [])):
               
            return 'IoT Device'
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
        nmap_services = device_data.get('nmap_services', [])

        # --- 2. Static IP Mapping Override (Highest Priority) ---
        static_info = None
        if ip_address and cls._is_static_ip(ip_address):
            static_info = cls._categorize_by_static_ip(ip_address)
            
        if static_info:
            # If a static entry is found, merge its data into the device data
            device_data.update(static_info)
            static_services_str = static_info.get('services', '')

            # If the static map provides a 'services' string, add them to the list for categorization.
            if static_services_str:
                static_services_list = [s.strip() for s in static_services_str.split(',')]
                nmap_services = list(dict.fromkeys(static_services_list + nmap_services))
        
        # --- 3. DHCP Scope Location Fallback (Medium Priority) ---        
        if 'location' not in device_data:
            dhcp_info = cls._get_location_from_dhcp_scope(ip_address)
            if dhcp_info and dhcp_info.get('location'):
                device_data['location'] = dhcp_info['location']
        
        # --- 4. Normalize Data for Comparison Logic ---    
        raw_name = (device_data.get('name') or device_data.get('deviceName') or '')
        raw_os = (device_data.get('os_platform') or device_data.get('operatingSystem') or '')
        
        raw_model = device_data.get('model') or ''
        if isinstance(raw_model, dict):
            raw_model = raw_model.get('name', '') or raw_model.get('model_number', '') or ''
        
        raw_mfr = device_data.get('manufacturer') or ''
        if isinstance(raw_mfr, dict):
            raw_mfr = raw_mfr.get('name', '') or ''
        
        # Hardware Normalization corrects for NIC vendors being misidentified as the manufacturer.
        norm_mfr, norm_model = cls._normalize_hardware_identity(str(raw_mfr), str(raw_model))
        
        # Update device_data so AssetMatcher uses the clean values.
        if norm_mfr != raw_mfr:
            device_data['manufacturer'] = norm_mfr
        if norm_model != raw_model:
            device_data['model'] = norm_model
        
        device_name = raw_name.lower()
        os_type = raw_os.lower()
        model = raw_model.lower()
        manufacturer = raw_mfr.lower()
        cloud_provider = cls._determine_cloud_provider(device_data)
        
        raw_serial = (device_data.get('serial') or '') # For easier search in logs
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
                cls._categorize_vm(manufacturer, model, device_name) or
                cls._categorize_iot(model, manufacturer, os_type, device_name) or
                cls._categorize_network_device(model, manufacturer, device_name) or
                cls._categorize_ios(os_type, model, device_name) or
                cls._categorize_android(os_type, model, manufacturer) or
                cls._categorize_computer(os_type, model, manufacturer, device_name) or
                cls._categorize_server(os_type, model, device_name) or
                (cls._categorize_by_services(nmap_services) if nmap_services else None) or
                cls._categorize_generic_os_device(os_type, model) or
                'Other Device'
            )

        # --- 6. Category Mapping ---
        # Use the category from the static map if available, otherwise map the device type.
        category = device_data.get('category') or categorization_rules.CATEGORY_MAP.get(device_type, 'Other Assets')
        if cloud_provider in ['Azure', 'AWS', 'GCP']:
            category = 'Cloud Resources'

        return {'device_type': device_type, 'category': category, 'cloud_provider': cloud_provider}