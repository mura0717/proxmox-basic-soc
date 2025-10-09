import os
import sys
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from debug.asset_debug_logger import debug_logger

class AssetCategorizer:
    """Determines device type and category based on attributes."""
    def __init__(self):
        pass
    
    NETWORK_DEVICE_RULES = {
        'Firewall': {
            'vendors': ['cisco', 'meraki', 'fortinet', 'palo alto', 'sonicwall', 'juniper', 'checkpoint'],
            'model_keywords': ['firewall', 'asa', 'srx', 'pa-', 'mx', 'security gateway', 'firepower']
        },
        'Switch': {
            'vendors': ['cisco', 'juniper', 'aruba', 'hp', 'dell', 'meraki', 'ubiquiti'],
            'model_keywords': ['switch', 'catalyst', 'nexus', 'comware', 'procurve', 'ex', 'ms', 'edgeswitch']
        },
        'Router': {
            'vendors': ['cisco', 'juniper', 'mikrotik', 'ubiquiti'],
            'model_keywords': ['router', 'isr', 'asr', 'edgerouter']
        },
        'Access Point': {
            'vendors': ['cisco', 'meraki', 'aruba', 'ubiquiti', 'ruckus'],
            'model_keywords': ['access point', 'ap', 'aironet', 'unifi', 'mr']
        }
    }
    
    @classmethod
    def _categorize_network_device(cls, model: str, manufacturer: str) -> str | None:
        """Categorizes network devices using a structured rule set."""
        device_type_priority = ['Firewall', 'Switch', 'Router', 'Access Point']

        for device_type in device_type_priority:
            rules = cls.NETWORK_DEVICE_RULES.get(device_type, {})
            
            if any(vendor in manufacturer for vendor in rules.get('vendors', [])):
                if any(keyword in model for keyword in rules.get('model_keywords', [])):
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
    def _is_laptop(cls, model: str, manufacturer: str) -> bool:
        """Check if device is a laptop, including Mac laptops"""
        laptop_markers = {
            'laptop', 'notebook', 'book', 'zenbook', 'vivobook',
            'thinkpad', 'latitude', 'xps', 'precision', 'elitebook',
            'probook', 'spectre', 'envy', 'surface laptop', 'studiobook',
            'proart', 'macbook', 'macbook pro', 'macbook air'
        }
        if any(marker in model for marker in laptop_markers):
            return True
        # Lenovo specific model numbers
        if manufacturer == 'lenovo' and any(model.startswith(prefix) for prefix in ['20', '21', '40']):
            return True

        return False
    
    @classmethod
    def _is_desktop(cls, model: str, manufacturer: str, os_type: str) -> bool:
        """Check if device is a desktop (includes workstations and Mac desktops)"""
        desktop_markers = {
            # General markers
            'desktop', 'workstation', 'station', 'studio',

            # Lenovo Specific Markers (from your list)
            'thinkcentre', 'ideacentre', 'thinkstation', 'neo', 'tower', 
            'sff', 'tiny', 'all-in-one', 'aio',
            # Adding specific model series can help too
            'm70s', 'm70t', 'm70q', 'm90s', 'm90t', 'm90q', 
            'm75s', 'm75t', 'm75q', 'p320', 'p520', 'p360', 'p340',

            # Mac specific
            'imac', 'mac mini', 'mac studio', 'mac pro',

            # Other OEM Workstations
            'zbook', 'z840', 'z640', 'z440', 'z240', 'z620', # HP
            'precision', # Dell (can be ambiguous, but often desktop workstations)
            'proart station' # Asus
        }
        if any(marker in model for marker in desktop_markers):
            return True
        if manufacturer == 'lenovo' and any(model.startswith(prefix) for prefix in ['10', '11', '12', '30']):
            return True
        if 'desktop' in os_type:
            return True
        return False

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
    def categorize(cls, device_data: Dict) -> Dict[str, str]:
        """Compute device_type and category from data."""
        
        # Extract source for logging
        source = device_data.get('_source', 'unknown')
        
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
        raw_serial = (device_data.get('serial') or '') # To easily search in log files / only present in debugging
        nmap_services = device_data.get('nmap_services', [])
        
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
            f"  Services:     {', '.join(nmap_services) if nmap_services else 'None'}\n"
            f"  Cloud Provider: {cloud_provider}\n"
            f"{'-'*50}\n"
        )
        debug_logger.log_categorization(source, log_entry)
        
        # Default device type
        device_type = 'Other Device'
        
        # PRIORITY 1: Network devices
        service_type = cls._categorize_by_services(nmap_services)
        if service_type and service_type not in ['Web Server', 'Network Device', 'Storage Device']:
            device_type = service_type
            
        # Priority 2: Specific network hardware
        elif cls._categorize_network_device(model, manufacturer):
            device_type = cls._categorize_network_device(model, manufacturer)
                            
        # PRIORITY 3: Virtual Machines
        elif any(m in manufacturer for m in ['vmware', 'virtualbox', 'qemu', 'microsoft corporation']) and ('virtual machine' in model or 'vm' in model):
            device_type = 'Virtual Machine'
            
        # PRIORITY 4: Servers
        elif 'server' in os_type or 'server' in model:
            device_type = 'Server'
            
        # PRIORITY 5: iOS devices
        elif 'ios' in os_type:
            if any(kw in model or kw in device_name for kw in ['ipad', 'ipad pro', 'ipad air', 'ipad mini']):
                device_type = 'Tablet'
            else:
                device_type = 'Mobile Phone'
        
        # PRIORITY 6: Android devices
        elif 'android' in os_type:
            if 'tablet' in model or 'tab' in model or manufacturer in ['samsung', 'lenovo', 'huawei']:
                device_type = 'Tablet'
            elif any(kw in model for kw in ['meetingbar', 'roompanel', 'ctp']):
                device_type = 'IoT Devices'
            else:
                device_type = 'Mobile Phone'
        
        # PRIORITY 7: Computers
        elif 'windows' in os_type or 'mac' in os_type:
            if cls._is_desktop(model, manufacturer, os_type):
                device_type = 'Desktop'
            elif cls._is_laptop(model, manufacturer):
                device_type = 'Laptop'
            else:
                device_type = 'Desktop'
        
        # PRIORITY 8: IoT Devices
        elif 'iot' in model or 'iot' in os_type:
            device_type = 'IoT Devices'
        else:
            device_type = device_type

        # Determine category (based on device_type and other attrs)
        if ('yealink' in manufacturer and any(x in model for x in ['roompanel', 'meetingbar', 'ctp', 'a20', 'a30'])) or 'iot' in device_type.lower():
            category = 'IoT Devices'
        elif 'server' in device_type.lower():
            category = 'Servers'
        elif 'switch' in device_type.lower():
            category = 'Switches'
        elif 'router' in device_type.lower():
            category = 'Routers'
        elif 'firewall' in device_type.lower():
            category = 'Firewalls'
        elif 'access point' in device_type.lower():
            category = 'Access Points'
        elif 'printer' in device_type.lower():
            category = 'Printers'
        elif 'laptop' in device_type.lower():
            category = 'Laptops'
        elif 'desktop' in device_type.lower():
            category = 'Desktops'
        elif 'tablet' in device_type.lower():
            category = 'Tablets'
        elif 'mobile phone' in device_type.lower() or 'mobile' in device_type.lower():
            category = 'Mobile Phones'
        elif 'virtual machine' in device_type.lower() or 'virtual' in device_type.lower() or 'vm' in device_type.lower():
            category = 'Virtual Machines (On-Premises)'
        elif cloud_provider in ['Azure', 'AWS', 'GCP']:
            category = 'Cloud Resources'
        else:
            category = 'Other Assets'

        return {'device_type': device_type, 'category': category, 'cloud_provider': cloud_provider}