# Paste your definitions from your existing script:
# CUSTOM_FIELDS, CUSTOM_FIELDSETS, STATUS_LABELS, CATEGORIES, LOCATIONS

CUSTOM_FIELDS = {
    # Identity / IDs
    'azure_ad_id': {"name": "Azure AD Device ID", "element": "text", "help_text": "Unique Identifier from Microsoft Entra ID (formerly Azure AD)"},
    'intune_device_id': {"name": "Intune Device ID", "element": "text", "help_text": "Unique Identifier from Intune"},
    'primary_user_id': {"name": "Primary User ID", "element": "text", "help_text": "Intune/AAD user object ID for the primary user"},

    # Enrollment / Management
    'intune_managed': {"name": "Intune Managed", "element": "checkbox", "help_text": "Is this device managed by Intune?"},
    'intune_registered': {"name": "Intune Registered", "element": "checkbox", "help_text": "Device is registered with Intune"},
    'intune_enrollment_date': {"name": "Intune Enrollment Date", "element": "text", "help_text": "Enrollment timestamp from Intune (ISO 8601)"},
    'intune_last_sync': {"name": "Intune Last Sync", "element": "text", "help_text": "Last check-in timestamp from Intune (ISO 8601)"},
    'managed_by': {"name": "Managed By", "element": "text", "help_text": "Management authority (e.g., Intune, Co-managed, ConfigMgr)"},
    'management_name': {"name": "Management Name", "element": "text", "help_text": "MDM management instance/name"},
    'intune_category': {"name": "Intune Category", "element": "text", "help_text": "Intune device category"},
    'ownership': {"name": "Ownership", "element": "text", "help_text": "Corporate or Personal ownership"},
    'device_state': {"name": "Device State", "element": "text", "help_text": "State reported by Intune (e.g., Active)"},
    'intune_compliance': {"name": "Intune Compliance", "element": "text", "help_text": "Compliance state (Compliant/Noncompliant/Unknown)"},
    'compliance_grace_expiration': {"name": "Compliance Grace Expiration", "element": "text", "help_text": "Compliance grace period expiration (ISO 8601)"},
    'management_cert_expiration': {"name": "Management Cert Expiration", "element": "text", "help_text": "Management certificate expiration date (ISO 8601)"},

    # OS / Platform
    'os_platform': {"name": "OS Platform", "element": "text", "help_text": "Operating system platform (e.g., Windows, macOS, iOS)"},
    'os_version': {"name": "OS Version", "element": "text", "help_text": "Specific OS version/build"},
    'sku_family': {"name": "SKU Family", "element": "text", "help_text": "OS SKU family/edition"},
    'join_type': {"name": "Join Type", "element": "text", "help_text": "AAD join type (AzureADJoined/Hybrid/Workgroup)"},
    'product_name': {"name": "Product Name", "element": "text", "help_text": "Product or OS name as reported"},
    'processor_architecture': {"name": "Processor Architecture", "element": "text", "help_text": "CPU architecture (x64, ARM64, etc.)"},
    'security_patch_level': {"name": "Security Patch Level", "element": "text", "help_text": "OS security patch level"},
    'encrypted': {"name": "Encrypted", "element": "checkbox", "help_text": "Device encryption status"},
    'supervised': {"name": "Supervised", "element": "checkbox", "help_text": "Supervised status (iOS/macOS)"},
    'jailbroken': {"name": "Jailbroken/Rooted", "element": "checkbox", "help_text": "Device jailbreak/root status"},
    'azure_ad_registered': {"name": "Azure AD Registered", "element": "checkbox", "help_text": "Registered in Azure AD"},
    'bios_version': {"name": "System Management BIOS Version", "element": "text", "help_text": "SMBIOS/Firmware version"},
    'tpm_manufacturer_id': {"name": "TPM Manufacturer ID", "element": "text", "help_text": "TPM manufacturer ID"},
    'tpm_manufacturer_version': {"name": "TPM Manufacturer Version", "element": "text", "help_text": "TPM manufacturer version"},

    # User
    'primary_user_upn': {"name": "Primary User UPN", "element": "text", "help_text": "User Principal Name of the primary user"},
    'primary_user_email': {"name": "Primary User Email", "element": "text", "help_text": "Primary user's email address"},
    'primary_user_display_name': {"name": "Primary User Display Name", "element": "text", "help_text": "Primary user's display name"},

    # Software Inventory
    'installed_software': {"name": "Installed Software", "element": "textarea", "help_text": "JSON list of installed applications from Intune"},
    'software_count': {"name": "Software Count", "element": "text", "help_text": "Total number of installed applications"},
    'last_software_scan': {"name": "Last Software Scan", "element": "text", "help_text": "Timestamp of last software inventory scan"},
    
    # Networking
    'dns_hostname': {"name": "DNS Hostname", "element": "text", "help_text": "Hostname from DNS or discovery"},
    'mac_addresses': {"name": "MAC Addresses", "element": "textarea", "help_text": "Newline-separated list of all MACs (Wi-Fi/Ethernet)"},
    'last_seen_ip': {"name": "Last Seen IP", "element": "text", "help_text": "Last observed IP on the network"},
    'intune_wifi_ipv4': {"name": "Intune WiFi IPv4", "element": "text", "help_text": "WiFi IPv4 address reported by Intune"},
    'wifi_subnet_id': {"name": "WiFi Subnet ID", "element": "text", "help_text": "WiFi subnet ID reported by Intune"},
    'wifi_mac': {"name": "WiFi MAC Address", "element": "text", "help_text": "MAC address for WiFi interface"},
    'ethernet_mac': {"name": "Ethernet MAC Address", "element": "text", "help_text": "MAC address for Ethernet interface"},
    'wifi_ipv4': {"name": "WiFi IPv4 Address", "element": "text", "help_text": "IPv4 address assigned to the WiFi interface"},
    'wifi_subnet': {"name": "WiFi Subnet", "element": "text", "help_text": "Subnet information for the WiFi interface"},
    
    # Network Device Information (SNMP)
    'device_type': {"name": "Device Type", "element": "text", "help_text": "Type: Computer, Switch, Router, Printer, IoT, etc."},
    'snmp_location': {"name": "SNMP Location", "element": "text", "help_text": "Physical location from SNMP"},
    'snmp_contact': {"name": "SNMP Contact", "element": "text", "help_text": "Contact person from SNMP"},
    'snmp_uptime': {"name": "SNMP Uptime", "element": "text", "help_text": "Device uptime from SNMP"},
    'switch_port_count': {"name": "Switch Port Count", "element": "text", "help_text": "Number of ports (for switches)"},
    'firmware_version': {"name": "Firmware Version", "element": "text", "help_text": "Firmware/IOS version for network devices"},

    # Cellular / Device comms
    'phone_number': {"name": "Phone Number", "element": "text", "help_text": "Device phone number (if available)"},
    'imei': {"name": "IMEI", "element": "text", "help_text": "International Mobile Equipment Identity"},
    'iccid': {"name": "ICCID", "element": "text", "help_text": "SIM card ICCID"},
    'meid': {"name": "MEID", "element": "text", "help_text": "Mobile Equipment Identifier"},
    'eid': {"name": "EID (eSIM)", "element": "text", "help_text": "Embedded SIM EID"},
    'subscriber_carrier': {"name": "Subscriber Carrier", "element": "text", "help_text": "Mobile carrier"},
    'cellular_technology': {"name": "Cellular Technology", "element": "text", "help_text": "e.g., LTE, 5G"},

    # Storage
    'total_storage': {"name": "Total Storage", "element": "text", "help_text": "Total device storage (bytes)"},
    'free_storage': {"name": "Free Storage", "element": "text", "help_text": "Free device storage (bytes)"},

    # EAS (Exchange ActiveSync)
    'eas_activation_id': {"name": "EAS Activation ID", "element": "text", "help_text": "EAS activation ID"},
    'eas_activated': {"name": "EAS Activated", "element": "checkbox", "help_text": "EAS activation status"},
    'eas_last_sync': {"name": "EAS Last Sync", "element": "text", "help_text": "Last EAS sync time (ISO 8601)"},
    'eas_reason': {"name": "EAS Reason", "element": "text", "help_text": "EAS status reason"},
    'eas_status': {"name": "EAS Status", "element": "text", "help_text": "EAS status"},

    # Nmap discovery
    'first_seen_date': {"name": "First Seen Date", "element": "text", "help_text": "Timestamp when first discovered (ISO 8601)"},
    'nmap_last_scan': {"name": "Nmap Last Scan", "element": "text", "help_text": "Timestamp of last nmap scan (ISO 8601)"},
    'nmap_os_guess': {"name": "Nmap OS Guess", "element": "text", "help_text": "Nmap's OS fingerprint guess"},
    'nmap_open_ports': {"name": "Nmap Open Ports", "element": "textarea", "help_text": "Newline or comma-separated list of open ports"},
    'open_ports_hash': {"name": "Open Ports Hash", "element": "text", "help_text": "Hash of open ports list to detect changes"},
    'discovery_note': {"name": "Discovery Note", "element": "textarea", "help_text": "Notes about discovery (VLAN, location, etc.)"},
    
    # Data hygiene
    'last_update_source': {"name": "Last Update Source", "element": "text", "help_text": "Which system updated last (Intune/Nmap/Azure)"},
    'last_update_at': {"name": "Last Update At", "element": "text", "help_text": "Timestamp of last update (ISO 8601)"},
    
    # Vulnerability Information
    'vulnerability_scan_date': {"name": "Last Vulnerability Scan", "element": "text", "help_text": "Date of last vulnerability scan"},
    'critical_vulns': {"name": "Critical Vulnerabilities", "element": "text", "help_text": "Count of critical vulnerabilities"},
    'high_vulns': {"name": "High Vulnerabilities", "element": "text", "help_text": "Count of high vulnerabilities"},
    'vulnerability_score': {"name": "Vulnerability Score", "element": "text", "help_text": "Overall vulnerability score (0-10)"},
    
    # Certificate Management
    'certificates': {"name": "Certificates", "element": "textarea", "help_text": "JSON list of certificates and expiry dates"},
    'cert_expiry_warning': {"name": "Certificate Expiry Warning", "element": "text", "help_text": "Earliest certificate expiry date"},
    
    # Asset Relationships
    'parent_device_id': {"name": "Parent Device ID", "element": "text", "help_text": "ID of parent device (for VMs, containers)"},
    'hypervisor_host': {"name": "Hypervisor Host", "element": "text", "help_text": "Host server for virtual machines"},
    'connected_switch_port': {"name": "Connected Switch Port", "element": "text", "help_text": "Switch and port this device connects to"},
    
    # Cloud Resource Information
    'cloud_provider': {"name": "Cloud Provider", "element": "text", "help_text": "Cloud provider (Azure, AWS, GCP, On-Premise)"},
    'azure_resource_id': {"name": "Azure Resource ID", "element": "text", "help_text": "ARM resource ID"},
    'azure_subscription_id': {"name": "Azure Subscription ID", "element": "text", "help_text": "Subscription GUID"},
    'azure_resource_group': {"name": "Azure Resource Group", "element": "text", "help_text": "Resource group name"},
    'azure_region': {"name": "Azure Region", "element": "text", "help_text": "Azure location/region"},
    'azure_tags_json': {"name": "Azure Tags (JSON)", "element": "textarea", "help_text": "JSON-encoded Azure tags"},
}

# Define which fields belong to which fieldset, using our reference keys
CUSTOM_FIELDSETS = {
    # Comprehensive fieldset for all managed assets
    "Managed Assets (Intune+Nmap)": [
        # Identity / IDs
        'azure_ad_id', 'intune_device_id', 'primary_user_id',

        # Enrollment / Management
        'intune_managed', 'intune_registered', 'intune_enrollment_date', 'intune_last_sync',
        'managed_by', 'management_name', 'intune_category', 'ownership', 'device_state',
        'intune_compliance', 'compliance_grace_expiration', 'management_cert_expiration',

        # OS / Platform
        'os_platform', 'os_version', 'sku_family', 'join_type', 'product_name',
        'processor_architecture', 'security_patch_level', 'encrypted', 'supervised',
        'jailbroken', 'azure_ad_registered', 'bios_version',
        'tpm_manufacturer_id', 'tpm_manufacturer_version',

        # User
        'primary_user_upn', 'primary_user_email', 'primary_user_display_name',

        # Networking
        'dns_hostname', 'mac_addresses', 'last_seen_ip', 'intune_wifi_ipv4', 'wifi_subnet_id',

        # Cellular / Device comms
        'phone_number', 'imei', 'iccid', 'meid', 'eid', 'subscriber_carrier', 'cellular_technology',

        # Storage
        'total_storage', 'free_storage',

        # EAS
        'eas_activation_id', 'eas_activated', 'eas_last_sync', 'eas_reason', 'eas_status',

        # Nmap
        'first_seen_date', 'nmap_last_scan', 'nmap_os_guess', 'nmap_open_ports', 'open_ports_hash',

        # Hygiene
        'last_update_source', 'last_update_at',
        
        # Notes
        'discovery_note',
    ],
    
    # Focused fieldset for core managed asset details
   "Managed Assets - Core Info": [
        'azure_ad_id', 'intune_device_id',
        'primary_user_upn', 'primary_user_display_name',
        'ownership', 'device_state', 'intune_compliance', 'intune_last_sync',
        'os_platform', 'os_version', 'product_name', 'device_type'
    ],
    
    # Focused fieldset for network and security details
    "Managed Assets - Network and Security": [
        'dns_hostname', 'mac_addresses', 'intune_wifi_ipv4', 'wifi_subnet_id', 'last_seen_ip',
        'encrypted', 'supervised', 'jailbroken', 'security_patch_level',
        'nmap_last_scan', 'nmap_open_ports', 'open_ports_hash', 'connected_switch_port'
    ],
    
    # Focused fieldset for hardware and system details
     "Managed Assets - Hardware Details": [
        'total_storage', 'free_storage', 'processor_architecture', 'tpm_manufacturer_id',
        'tpm_manufacturer_version', 'bios_version', 'sku_family', 'parent_device_id', 'hypervisor_host'
    ],
     
    # Software inventory details
    "Software and Applications": [
        'installed_software', 'software_count', 'last_software_scan'
    ],
    # Vulnerability and certificate details
    "Security and Vulnerabilities": [
        'vulnerability_scan_date', 'critical_vulns', 'high_vulns', 'vulnerability_score',
        'certificates', 'cert_expiry_warning', 'security_patch_level', 'encrypted'
    ],
    
    # Network devices and infrastructure
     "Network Infrastructure": [
        'device_type', 'snmp_location', 'snmp_contact', 'snmp_uptime',
        'switch_port_count', 'firmware_version', 'dns_hostname', 'mac_addresses', 'connected_switch_port',
    ],
    
    # Cellular and mobile device specifics
    "Mobile Devices": [
        'imei', 'meid', 'phone_number', 'iccid', 'eid', 'subscriber_carrier',
        'cellular_technology', 'supervised', 'jailbroken'
    ],
    
    # Nmap-discovered assets
    "Discovered Assets (Nmap Only)": [
        'dns_hostname', 'mac_addresses', 'last_seen_ip',
        'first_seen_date', 'nmap_last_scan', 'nmap_os_guess',
        'nmap_open_ports', 'open_ports_hash', 'discovery_note', 'device_type'
    ],
    
    # Cloud resources
    "Cloud Resources (Azure)": [
        'cloud_provider', 'azure_resource_id', 'azure_subscription_id', 'azure_resource_group',
        'azure_region', 'azure_tags_json', 'last_update_source', 'last_update_at'
    ],
    
    # All network identifiers for easy reference
    "All Network Identifiers": [
        'dns_hostname', 'wifi_mac', 'ethernet_mac', 'mac_addresses', 'wifi_ipv4',
        'wifi_subnet', 'last_seen_ip', 'connected_switch_port'
    ]
}

# Define Status Labels
STATUS_LABELS = {
    "Managed (Intune)": {
        "type": "deployable", 
        "color": "#3498db",
        "show_in_nav": False,
        "default_label": False
        },
    "Discovered (Nmap)": {
        "type": "deployable", 
        "color": "#f1c40f",
        "show_in_nav": False,
        "default_label": False
        },
    "Cloud Resource": {
        "type": "deployable", 
        "color": "#9b59b6",
        "show_in_nav": False,
        "default_label": False
    },
    "On-Premise": {
        "type": "deployable", 
        "color": "#008000",
        "show_in_nav": False,
        "default_label": False
    },
    "Off-site": {
        "type": "deployable", 
        "color": "#e67e22",
        "show_in_nav": False,
        "default_label": False
    },
    "Unmanaged/Discovered": {
        "type": "deployable", 
        "color": "#e74c3c",
        "show_in_nav": False,
        "default_label": False
    },
    "Unknown": {
        "type": "deployable", 
        "color": "#95a5a6",
        "show_in_nav": False,
        "default_label": True
    },
    "Missing": {
        "type": "deployable", 
        "color": "#000000",
        "show_in_nav": False,
        "default_label": False
    },
}

# Define Categories
CATEGORIES = {
    "Desktops": {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
    },
    "Laptops" : {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
    },
    "Tablets" : {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
    }, 
    "Mobile Phones" : {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
        },
    "Monitors": {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
        },
    "Storage Devices": {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
        },
    "Servers": {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
    },
     "Network Devices": {
        "category_type": "asset",
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
    },
    "Printers": {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
        },
    "IoT Devices": {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
        },
    "Virtual Machines (On-Premises)": {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
        },
    "Cloud Resources": {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
        },
    "Software Licenses": {
        "category_type": "license",
        "use_default_eula": True,
        "require_acceptance": True,
        "checkin_email": False
    },
       "Other Assets": {
        "category_type": "asset", 
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
        },
}

# Define Generic Models
MODELS = [
    {'name': 'Generic Device', 'category': 'Other Assets', 'manufacturer': 'Generic'},
    {'name': 'Generic Desktop', 'category': 'Desktops', 'manufacturer': 'Generic'},
    {'name': 'Generic Laptop', 'category': 'Laptops', 'manufacturer': 'Generic'},
    {'name': 'Generic Server', 'category': 'Servers', 'manufacturer': 'Generic'},
    {'name': 'Generic Network Device', 'category': 'Network Devices', 'manufacturer': 'Generic'},
    {'name': 'Generic Printer', 'category': 'Printers', 'manufacturer': 'Generic'},
    {'name': 'Generic Mobile Phone', 'category': 'Mobile Phones', 'manufacturer': 'Generic'},
    {'name': 'Generic IoT Device', 'category': 'IoT Devices', 'manufacturer': 'Generic'},
    {'name': 'Generic Storage Device', 'category': 'Storage Devices', 'manufacturer': 'Generic'},
    {'name': 'Generic Virtual Machine', 'category': 'Virtual Machines (On-Premises)', 'manufacturer': 'Generic'},
    {'name': 'Generic Cloud Resource', 'category': 'Cloud Resources', 'manufacturer': 'Generic'},
    {'name': 'Generic Software License', 'category': 'Software Licenses', 'manufacturer': 'Generic'},
]

#Define Manufacturers
MANUFACTURERS = [
    {'name': 'Generic', 'support_contact': '', 'support_url': ''},
    {'name': 'Apple', 'support_contact': '1-800-MY-APPLE', 'support_url': 'https://support.apple.com/'},
    {'name': 'Dell', 'support_contact': '1-800-624-9897', 'support_url': 'https ://www.dell.com/support/home/en-us'},
    {'name': 'HP', 'support_contact': '1-800-474-6836', 'support_url': 'https://support.hp.com/'},
    {'name': 'Lenovo', 'support_contact': '1-855-253-6686', 'support_url': 'https://support.lenovo.com/'},
    {'name': 'Microsoft', 'support_contact': '1-800-642-7676', 'support_url': 'https://support.microsoft.com/'},
    {'name': 'Cisco', 'support_contact': '1-800-553-2447', 'support_url': 'https://www.cisco.com/c/en/us/support/index.html'},
    {'name': 'Samsung', 'support_contact': '1-800-SAMSUNG', 'support_url': 'https://www.samsung.com/us/support/'},
    {'name': 'Asus', 'support_contact': '1-888-678-3688', 'support_url': 'https://www.asus.com/support/'},
    {'name': 'Acer', 'support_contact': '1-866-695-2237', 'support_url': 'https://www.acer.com/ac/en/US/content/support'},
    {'name': 'LG', 'support_contact': '1-800-243-0000', 'support_url': 'https://www.lg.com/us/support'},
    {'name': 'Sony', 'support_contact': '1-800-222-7669', 'support_url': 'https://www.sony.com/electronics/support'},
    {'name': 'Toshiba', 'support_contact': '1-800-457-7777', 'support_url': 'https://support.dynabook.com/'},
    {'name': 'VMware', 'support_contact': '1-877-486-9273', 'support_url': 'https://www.vmware.com/support.html'},
    {'name': 'Citrix', 'support_contact': '1-800-424-8749', 'support_url': 'https://www.citrix.com/support/'},
    {'name': 'Red Hat', 'support_contact': '1-866-273-3424', 'support_url': 'https://access.redhat.com/support'},
    {'name': 'Juniper Networks', 'support_contact': '1-888-314-5822', 'support_url': 'https://www.juniper.net/us/en/support/'},
    {'name': 'Hewlett Packard Enterprise', 'support_contact': '1-800-633-3600', 'support_url': 'https://www.hpe.com/us/en/support.html'},
    {'name': 'NetApp', 'support_contact': '1-888-463-8277', 'support_url': 'https://www.netapp.com/support/'},
    {'name': 'Fujitsu', 'support_contact': '1-800-831-3183', 'support_url': 'https://www.fujitsu.com/global/support/'},
    {'name': 'Panasonic', 'support_contact': '1-800-662-3537', 'support_url': 'https://www.panasonic.com/global/support.html'},
    {'name': 'Brother', 'support_contact': '1-877-755-2526', 'support_url': 'https://www.brother-usa.com/support'},
    {'name': 'Epson', 'support_contact': '1-800-463-7766', 'support_url': 'https://epson.com/support'},
    {'name': 'Zebra Technologies', 'support_contact': '1-800-423-0442', 'support_url': 'https://www.zebra.com/us/en/support.html'},
    {'name': 'Poly', 'support_contact': '1-800-289-9100', 'support_url': 'https://www.poly.com/us/en/support'},
    {'name': 'Logitech', 'support_contact': '1-646-454-3200', 'support_url': 'https://support.logi.com/hc/en-us'},
    {'name': 'Razer', 'support_contact': '1-888-204-4590', 'support_url': 'https://www.razer.com/support'},
    {'name': 'Dell EMC', 'support_contact': '1-800-624-9897', 'support_url': 'https://www.dell.com/support/home/en-us'},
    {'name': 'Supermicro', 'support_contact': '1-408-503-8000', 'support_url': 'https://www.supermicro.com/support/'},
    {'name': 'Aruba Networks', 'support_contact': '1-800-943-4526', 'support_url': 'https://www.arubanetworks.com/support/'},
    {'name': 'Extreme Networks', 'support_contact': '1-888-257-3000', 'support_url': 'https://www.extremenetworks.com/support/'},
    {'name': 'Ubiquiti', 'support_contact': '1-408-942-3080', 'support_url': 'https://www.ui.com/support/'},
    {'name': 'TP-Link', 'support_contact': '1-866-225-8139', 'support_url': 'https://www.tp-link.com/us/support/'},
    {'name': 'Netgear', 'support_contact': '1-888-638-4327', 'support_url': 'https://www.netgear.com/support/'},
    {'name': 'D-Link', 'support_contact': '1-877-453-5465', 'support_url': 'https://support.dlink.com/'},
    {'name': 'Linksys', 'support_contact': '1-800-326-7114', 'support_url': 'https://www.linksys.com/us/support/'},
    {'name': 'Citrix', 'support_contact': '1-800-424-8749', 'support_url': 'https://www.citrix.com/support/'},
]

# Define Locations
LOCATIONS = {
    "Glostrup Office - Home",
    "Odense Office",
    "Off-site",
    "Cloud"
}