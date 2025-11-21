"""
Centralized Rule Definitions for Asset Categorization
"""

NIC_VENDORS = {
    'liteon', 'universal global scientific industrial', 'intel', 'realtek', 
    'lcfc(hefei) electronics technology', 'hon hai precision', 'murata', 'azurewave'
}

NETWORK_DEVICE_RULES = {
    'Firewall': {
        'vendors': ['cisco', 'meraki', 'fortinet', 'palo alto', 'sonicwall', 'juniper', 'checkpoint', 'sophos'],
        'model_keywords': ['firewall', 'asa', 'srx', 'pa-', 'mx', 'security gateway', 'firepower']
    },
    'Switch': {
        'vendors': ['cisco', 'juniper', 'aruba', 'hp', 'dell', 'meraki', 'ubiquiti', 'd-link', 'netgear', 'tp-link'],
        'model_keywords': ['switch', 'catalyst', 'nexus', 'comware', 'procurve', 'ex', 'ms', 'edgeswitch', 'unifi switch', 'dgs', 'sg', 'usw'],
        'hostname_prefixes': ['sw', 'switch', 'tl', 'tl-', 'tl-sg', 'hp-switch', 'dgs-'] 
    },
    'Router': {
        'vendors': ['cisco', 'juniper', 'mikrotik', 'ubiquiti', 'netgear', 'tp-link'],
        'model_keywords': ['router', 'isr', 'asr', 'edgerouter', 'unifi gateway']
    },
    'Access Point': {
        'vendors': ['cisco', 'meraki', 'aruba', 'ubiquiti', 'ruckus', 'tp-link', 'unifi'],
        'model_keywords': ['access point', 'ap', 'aironet', 'unifi', 'mr', 'wap'],
        'hostname_prefixes': ['ap', 'ap-', 'ap1', 'ap2', 'ap3', 'ap4', 'ap5', 'ap6', 'ap7', 'ap8', 'uap']
    }
}

VIRTUAL_MACHINE_RULES = {
    'vendors': ['vmware', 'virtualbox', 'qemu', 'microsoft corporation'],
    'model_keywords': ['virtual machine', 'vm'],
    'hostname_keywords': ['kaanubuntu', 'zabbix-proxy.diabetes.local'] # Temporary
}

SERVER_RULES = {
    'os_keywords': ['windows server', 'esxi'],
    'model_keywords': ['server'],
    'hostname_keywords': ['zabbix', 'ubuntu', 'veeam', 'vcenter', 'esx', 'dc', 'filesrvr', 'terminal', 'consult']
}

IOS_RULES = {
    'tablet_keywords': ['ipad', 'ipad pro', 'ipad air', 'ipad mini'],
    'phone_keywords': ['iphone'],
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
        'proart', 'macbook', 'macbook pro', 'macbook air',
    },
    'laptop_hostname_keywords': {'laptop', 'book', 'mob', 'nb'},
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
    'desktop_hostname_keywords': {'pc', 'desktop', 'wkst', 'workstation'},
    'desktop_vendor_prefixes': {
        'lenovo': ['10', '11', '12', '30']
    },
    'desktop_os_keywords': ['desktop', 'windows workstation', 'linux workstation']
}

IOT_RULES = {
    'manufacturer_keywords': ['yealink'],
    'model_keywords': ['iot', 'meetingbar', 'roompanel', 'ctp', 'ctp18', 'a20', 'a30', 'poly', 'core2kit'],
    'hostname_keywords': ['meetingbar', 'roompanel', 'ctp', 'poly'],
    'os_keywords': ['iot', 'androidaosp']
}

SERVICE_RULES = {
    'Domain Controller': {
        'service_keywords': ['domain', 'ldap', 'kerberos']
    },
    'Printer': {
        'service_keywords': ['ipp', 'jetdirect', 'printer', 'cups', 'lpr']
    },
    'Database Server': {
        'service_keywords': ['mysql', 'mssql', 'postgresql', 'oracle', 'mongodb']
    },
    'Storage Device': {
        'service_keywords': ['nfs', 'smb', 'cifs', 'iscsi', 'netapp', 'synology']
    },
    'Web Server': {
        'service_keywords': ['http', 'https', 'nginx', 'apache', 'iis']
    },
    'Network Device': { 
        'service_keywords': ['snmp']
    }
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
    'Virtual Machine': 'Virtual Machines',
    'IoT Device': 'IoT Devices',
    # Map inferred models to existing categories
    'Windows Server': 'Servers',
    'Linux Server': 'Servers',
    'Windows Workstation': 'Desktops',
    'Linux Workstation': 'Desktops',
    'macOS Device': 'Desktops',
}