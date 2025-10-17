"""
Centralized Rule Definitions for Asset Categorization
"""

NETWORK_DEVICE_RULES = {
    'Firewall': {
        'vendors': ['cisco', 'meraki', 'fortinet', 'palo alto', 'sonicwall', 'juniper', 'checkpoint', 'sophos'],
        'model_keywords': ['firewall', 'asa', 'srx', 'pa-', 'mx', 'security gateway', 'firepower']
    },
    'Switch': {
        'vendors': ['cisco', 'juniper', 'aruba', 'hp', 'dell', 'meraki', 'ubiquiti', 'd-link', 'netgear', 'tp-link'],
        'model_keywords': ['switch', 'catalyst', 'nexus', 'comware', 'procurve', 'ex', 'ms', 'edgeswitch', 'dgs', 'sg', 'tl-sg']
    },
    'Router': {
        'vendors': ['cisco', 'juniper', 'mikrotik', 'ubiquiti', 'netgear', 'tp-link'],
        'model_keywords': ['router', 'isr', 'asr', 'edgerouter']
    },
    'Access Point': {
        'vendors': ['cisco', 'meraki', 'aruba', 'ubiquiti', 'ruckus', 'tp-link'],
        'model_keywords': ['access point', 'ap', 'aironet', 'unifi', 'mr']
    }
}

VIRTUAL_MACHINE_RULES = {
    'vendors': ['vmware', 'virtualbox', 'qemu', 'microsoft corporation'],
    'model_keywords': ['virtual machine', 'vm']
}

SERVER_RULES = {
    'os_keywords': ['server'],
    'model_keywords': ['server']
}

IOS_RULES = {
    'tablet_keywords': ['ipad', 'ipad pro', 'ipad air', 'ipad mini'],
    'phone_keywords': ['iphone']
}

ANDROID_RULES = {
    'tablet_keywords': ['tablet', 'tab'],
    'tablet_vendors': ['samsung', 'lenovo', 'huawei'],
    'iot_keywords': ['meetingbar', 'roompanel', 'ctp']
}

COMPUTER_RULES = {
    'laptop_keywords': {
        'laptop', 'notebook', 'book', 'zenbook', 'vivobook',
        'thinkpad', 'latitude', 'xps', 'precision', 'elitebook',
        'probook', 'spectre', 'envy', 'surface laptop', 'studiobook',
        'proart', 'macbook', 'macbook pro', 'macbook air'
    },
    'laptop_vendor_prefixes': {
        'lenovo': ['20', '21', '40']
    },
    'desktop_keywords': {
        'desktop', 'workstation', 'station', 'studio', 'thinkcentre', 
        'ideacentre', 'thinkstation', 'neo', 'tower', 'sff', 'tiny', 
        'all-in-one', 'aio', 'm70s', 'm70t', 'm70q', 'm90s', 'm90t', 
        'm90q', 'm75s', 'm75t', 'm75q', 'p320', 'p520', 'p360', 'p340',
        'imac', 'mac mini', 'mac studio', 'mac pro', 'zbook', 'z840', 
        'z640', 'z440', 'z240', 'z620', 'precision', 'proart station'
    },
    'desktop_vendor_prefixes': {
        'lenovo': ['10', '11', '12', '30']
    },
    'desktop_os_keywords': ['desktop', 'windows workstation', 'linux workstation']
}

IOT_RULES = {
    'model_keywords': ['iot', 'meetingbar', 'roompanel', 'ctp', 'a20', 'a30'],
    'os_keywords': ['iot', 'android'] # Android is often used for IoT
}

CATEGORY_MAP = {
    'Server': 'Servers',
    'Switch': 'Switches',
    'Router': 'Routers',
    'Firewall': 'Firewalls',
    'Access Point': 'Access Points',
    'Printer': 'Printers',
    'Laptop': 'Laptops',
    'Desktop': 'Desktops',
    'Tablet': 'Tablets',
    'Mobile Phone': 'Mobile Phones',
    'Virtual Machine': 'Virtual Machines (On-Premises)',
    'IoT Devices': 'IoT Devices',
    # Map inferred models to existing categories
    'Windows Server': 'Servers',
    'Linux Server': 'Servers',
    'Windows Workstation': 'Desktops',
    'Linux Workstation': 'Desktops',
    'macOS Device': 'Desktops',
}