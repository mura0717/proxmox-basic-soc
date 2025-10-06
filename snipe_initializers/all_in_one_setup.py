import os
import requests
from dotenv import load_dotenv
import urllib3
import json
import time

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
# Only for testing when self-signed certs are used.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config_path = "/opt/snipeit-sync/snipe-it-asset-management/.env"
load_dotenv(dotenv_path=config_path)

SNIPE_URL = (os.getenv("SNIPE_URL") or "").rstrip("/")
SNIPE_API_TOKEN = os.getenv("SNIPE_API_TOKEN")

# URL & API TOKEN debug  
#print(f"Loaded Snipe URL: {SNIPE_URL}")
#print(f"Loaded Snipe API TOKEN: {SNIPE_API_TOKEN}")

if not SNIPE_URL or not SNIPE_API_TOKEN:
    raise RuntimeError("SNIPE_URL and SNIPE_API_TOKEN must be set.")

HEADERS = {
    "Authorization": f"Bearer {SNIPE_API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json", 
}

VERIFY_SSL = False # Set to True in production if using valid certs

# Define ALL unique fields that will be needed across ALL fieldsets
CUSTOM_FIELDS = {
    # Identity / IDs
    'azure_ad_id': {"name": "Azure AD Device ID", "element": "text", "help_text": "Unique Identifier from Microsoft Entra ID (formerly Azure AD)"},
    'intune_device_id': {"name": "Intune Device ID", "element": "text", "help_text": "Unique Identifier from Intune"},
    'primary_user_id': {"name": "Primary User ID", "element": "text", "help_text": "Intune/AAD user object ID for the primary user"},
    'device_enrollment_type': {"name": "Device Enrollment Type", "element": "text", "help_text": "Type of device enrollment"},
    'device_registration_state': {"name": "Device Registration State", "element": "text", "help_text": "State of device registration"},
    'device_category_display_name': {"name": "Device Category Display Name", "element": "text", "help_text": "Display name of the device category"},
    'udid': {"name": "UDID", "element": "text", "help_text": "Unique Device Identifier"},
    'serial_number': {"name": "Serial Number", "element": "text", "help_text": "Serial number of the device"},

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
    'enrollment_profile_name': {"name": "Enrollment Profile Name", "element": "text", "help_text": "Name of the enrollment profile used"},
    'require_user_enrollment_approval': {"name": "Require User Enrollment Approval", "element": "checkbox", "help_text": "Indicates if user enrollment approval is required"},
    'activation_lock_bypass_code': {"name": "Activation Lock Bypass Code", "element": "text", "help_text": "Bypass code for activation lock"},

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
    'android_security_patch_level': {"name": "Android Security Patch Level", "element": "text", "help_text": "Security patch level for Android devices"},
    'model': {"name": "Model", "element": "text", "help_text": "Device model"},
    'manufacturer': {"name": "Manufacturer", "element": "text", "help_text": "Device manufacturer"},

    # User
    'primary_user_upn': {"name": "Primary User UPN", "element": "text", "help_text": "User Principal Name of the primary user"},
    'primary_user_email': {"name": "Primary User Email", "element": "text", "help_text": "Primary user's email address"},
    'primary_user_display_name': {"name": "Primary User Display Name", "element": "text", "help_text": "Primary user's display name"},
    'user_display_name': {"name": "User Display Name", "element": "text", "help_text": "Display name of the user"},

    # Software Inventory
    'installed_software': {"name": "Installed Software", "element": "textarea", "help_text": "JSON list of installed applications from Intune"},
    'software_count': {"name": "Software Count", "element": "text", "help_text": "Total number of installed applications"},
    'last_software_scan': {"name": "Last Software Scan", "element": "text", "help_text": "Timestamp of last software inventory scan"},
    'configuration_manager_client_enabled_features': {"name": "Configuration Manager Client Enabled Features", "element": "text", "help_text": "Enabled features for Configuration Manager client"},

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
    'physical_memory_in_bytes': {"name": "Physical Memory (Bytes)", "element": "text", "help_text": "Total physical memory in bytes"},

    # EAS (Exchange ActiveSync)
    'eas_activation_id': {"name": "EAS Activation ID", "element": "text", "help_text": "EAS activation ID"},
    'eas_activated': {"name": "EAS Activated", "element": "checkbox", "help_text": "EAS activation status"},
    'eas_last_sync': {"name": "EAS Last Sync", "element": "text", "help_text": "Last EAS sync time (ISO 8601)"},
    'eas_reason': {"name": "EAS Reason", "element": "text", "help_text": "EAS status reason"},
    'eas_status': {"name": "EAS Status", "element": "text", "help_text": "EAS status"},
    'exchange_last_successful_sync_date_time': {"name": "Exchange Last Successful Sync DateTime", "element": "text", "help_text": "Date and time of the last successful Exchange sync"},
    'exchange_access_state': {"name": "Exchange Access State", "element": "text", "help_text": "Current state of Exchange access"},
    'exchange_access_state_reason': {"name": "Exchange Access State Reason", "element": "text", "help_text": "Reason for the current Exchange access state"},
    'remote_assistance_session_url': {"name": "Remote Assistance Session URL", "element": "text", "help_text": "URL for remote assistance session"},
    'remote_assistance_session_error_details': {"name": "Remote Assistance Session Error Details", "element": "text", "help_text": "Error details for remote assistance session"},

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
    'device_action_results': {"name": "Device Action Results", "element": "textarea", "help_text": "Results of device actions performed"},
    'device_health_attestation_state': {"name": "Device Health Attestation State", "element": "text", "help_text": "State of device health attestation"},
    'partner_reported_threat_state': {"name": "Partner Reported Threat State", "element": "text", "help_text": "Threat state reported by partner"},
    'notes': {"name": "Notes", "element": "textarea", "help_text": "Additional notes about the device"},

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
        'azure_ad_id', 'intune_device_id', 'primary_user_id', 'device_enrollment_type', 'device_registration_state', 'device_category_display_name', 'udid', 'serial_number',

        # Enrollment / Management
        'intune_managed', 'intune_registered', 'intune_enrollment_date', 'intune_last_sync',
        'managed_by', 'management_name', 'intune_category', 'ownership', 'device_state',
        'intune_compliance', 'compliance_grace_expiration', 'management_cert_expiration',
        'enrollment_profile_name', 'require_user_enrollment_approval', 'activation_lock_bypass_code',

        # OS / Platform
        'os_platform', 'os_version', 'sku_family', 'join_type', 'product_name',
        'processor_architecture', 'security_patch_level', 'encrypted', 'supervised',
        'jailbroken', 'azure_ad_registered', 'bios_version',
        'tpm_manufacturer_id', 'tpm_manufacturer_version', 'android_security_patch_level', 'model', 'manufacturer',

        # User
        'primary_user_upn', 'primary_user_email', 'primary_user_display_name', 'user_display_name',

        # Software Inventory
        'installed_software', 'software_count', 'last_software_scan', 'configuration_manager_client_enabled_features',

        # Networking
        'dns_hostname', 'mac_addresses', 'last_seen_ip', 'intune_wifi_ipv4', 'wifi_subnet_id',

        # Cellular / Device comms
        'phone_number', 'imei', 'iccid', 'meid', 'eid', 'subscriber_carrier', 'cellular_technology',

        # Storage
        'total_storage', 'free_storage', 'physical_memory_in_bytes',

        # EAS
        'eas_activation_id', 'eas_activated', 'eas_last_sync', 'eas_reason', 'eas_status',

        # Nmap
        'first_seen_date', 'nmap_last_scan', 'nmap_os_guess', 'nmap_open_ports', 'open_ports_hash',

        # Hygiene
        'last_update_source', 'last_update_at', 'device_action_results', 'device_health_attestation_state', 'partner_reported_threat_state', 'notes',

        # Notes
        'discovery_note',
    ],

    # Focused fieldset for core managed asset details
    "Managed Assets - Core Info": [
        'azure_ad_id', 'intune_device_id', 'primary_user_upn', 'primary_user_display_name',
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
        'installed_software', 'software_count', 'last_software_scan', 'configuration_manager_client_enabled_features'
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
    ],
    
       # Exchange and Remote Assistance
    "Exchange and Remote Assistance": [
        'exchange_last_successful_sync_date_time',
        'exchange_access_state',
        'exchange_access_state_reason',
        'remote_assistance_session_url',
        'remote_assistance_session_error_details'
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
    "Firewalls": {
        "category_type": "asset",
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
    },
    "Switches": {
        "category_type": "asset",
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
    },
    "Routers": {
        "category_type": "asset",
        "use_default_eula": False,
        "require_acceptance": False,
        "checkin_email": False
    },
    "Access Points": {
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
    {'name': 'Generic Firewall', 'category': 'Firewalls', 'manufacturer': 'Generic'},
    {'name': 'Generic Switch', 'category': 'Switches', 'manufacturer': 'Generic'},
    {'name': 'Generic Router', 'category': 'Routers', 'manufacturer': 'Generic'},
    {'name': 'Generic Access Point', 'category': 'Access Points', 'manufacturer': 'Generic'},
    {'name': 'Generic Network Device', 'category': 'Network Devices', 'manufacturer': 'Generic'},
    {'name': 'Generic Printer', 'category': 'Printers', 'manufacturer': 'Generic'},
    {'name': 'Generic Mobile Phone', 'category': 'Mobile Phones', 'manufacturer': 'Generic'},
    {'name': 'Generic Tablet', 'category': 'Tablets', 'manufacturer': 'Generic'},
    {'name': 'Generic IoT Device', 'category': 'IoT Devices', 'manufacturer': 'Generic'},
    {'name': 'Generic Storage Device', 'category': 'Storage Devices', 'manufacturer': 'Generic'},
    {'name': 'Generic Virtual Machine', 'category': 'Virtual Machines (On-Premises)', 'manufacturer': 'Generic'},
    {'name': 'Generic Cloud Resource', 'category': 'Cloud Resources', 'manufacturer': 'Generic'},
    {'name': 'Generic Software License', 'category': 'Software Licenses', 'manufacturer': 'Generic'},
]

#Define Manufacturers
MANUFACTURERS = [
    {'name': 'Generic', 'support_contact': '', 'support_url': ''}
]

# Define Locations
LOCATIONS = {
    "Glostrup Office - Home",
    "Odense Office",
    "Off-site",
    "Cloud"
}

def make_api_request(method, url, max_retries=3, **kwargs):
    # Helper function to make API requests with retry logic
    for attempt in range(max_retries+1): # +1 to include initial attempt
        try:
            response = requests.request(method, url, headers=HEADERS, verify=VERIFY_SSL, **kwargs)
            if response.status_code == 429:
                if attempt < max_retries:
                    try:
                        error_data = response.json()
                        retry_after = int(error_data.get("retryAfter", 15)) + 1
                    except (ValueError, json.JSONDecodeError):
                        retry_after = 15 # Default if parsing fails
                    print(f"-> Rate limited on {method} {url}. Retrying in {retry_after}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"-> Max retries exceeded for {method} {url}. Aborting this request.")
                    response.raise_for_status() # Raise the final 429 error

            # For any other non-successful status code, raise an exception
            response.raise_for_status()
            
            return response

        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                print(f"-> Network error ({e}). Retrying in 10s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(10)
            else:
                print(f"-> A persistent network error occurred. Aborting.")
                raise e
    return None
                        
def get_allfields_map():
    """Fetches all fields from Snipe-IT. Now automatically robust."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/fields", params={"limit": 5000})
    return {field['name']: int(field['id']) for field in response.json().get("rows", [])} if response else {}

def get_allfieldsets_map():
    """Fetches all fieldsets from Snipe-IT. Now automatically robust."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/fieldsets", params={"limit": 5000})
    return {fs['name']: int(fs['id']) for fs in response.json().get("rows", [])} if response else {}

def get_fieldset_fields(fieldset_id):
    """Fetch fields currently associated with a fieldset."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/fieldsets/{fieldset_id}/fields")
    if response:
        return {field['id'] for field in response.json().get("rows", [])}
    return set()

def get_status_labels_map():
    """Fetches all status labels from Snipe-IT."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/statuslabels", params={"limit": 5000})
    return {label['name']: label['id'] for label in response.json().get("rows", [])} if response else {}

def get_categories_map():
    """Fetches all categories from Snipe-IT."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/categories", params={"limit": 5000})
    return {cat['name']: cat['id'] for cat in response.json().get("rows", [])} if response else {}
  
def get_models_map():
    """Fetches all models from Snipe-IT."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/models", params={"limit": 5000})
    return {model['name']: model['id'] for model in response.json().get("rows", [])} if response else {}

def get_manufacturers_map():
    """Fetches all manufacturers from Snipe-IT."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/manufacturers", params={"limit": 5000})
    return {manu['name']: manu['id'] for manu in response.json().get("rows", [])} if response else {}
          
def get_location_map():
    """Fetches all locations from Snipe-IT."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/locations", params={"limit": 5000})
    return {loc['name']: loc['id'] for loc in response.json().get("rows", [])} if response else {}

def create_all_fields():
    """Creates all defined custom fields if they don't already exist."""
    print("\n--- Creating Custom Fields ---")
    existing_fields = set(get_allfields_map().keys())

    for field_data in CUSTOM_FIELDS.values():
        if field_data["name"] in existing_fields:
            print(f"Field '{field_data['name']}' already exists. Skipping.") # Uncomment for less output
            continue
        print(f"Creating field: {field_data['name']}...")
        make_api_request("POST", f"{SNIPE_URL}/api/v1/fields", json=field_data)
    print("Custom field creation process complete.")

def create_all_fieldsets():
    """Creates all defined fieldsets if they don't already exist."""
    print("\n--- Creating Fieldsets ---")
    existing_fieldsets = set(get_allfieldsets_map().keys())
    
    for name in CUSTOM_FIELDSETS.keys():
        if name in existing_fieldsets:
            print(f"Fieldset '{name}' already exists. Skipping.")
            continue
        
        print(f"Creating fieldset: {name}...")
        make_api_request("POST", f"{SNIPE_URL}/api/v1/fieldsets", json={"name": name})
    print("Fieldset creation process complete.")
            
def associate_fields_to_fieldsets():
    """Associates all defined fields with their respective fieldsets."""
    print("\n--- Associating Fields with Fieldsets ---")

    all_fields_map = get_allfields_map()
    all_fieldsets_map = get_allfieldsets_map()

    if not all_fields_map or not all_fieldsets_map:
        print("ERROR: Could not get field and/or fieldset maps. Aborting association.")
        return

    for fs_name, field_keys in CUSTOM_FIELDSETS.items():
        fieldset_id = all_fieldsets_map.get(fs_name)
        
        if not fieldset_id:
            print(f"WARNING: Fieldset '{fs_name}' was not found on the server. Skipping association for it.")
            continue
    
        print(f"Processing associations for fieldset '{fs_name}' (ID: {fieldset_id})...")
        
        for key in field_keys:
            field_def = CUSTOM_FIELDS.get(key, {})
            field_name = field_def.get('name')
            
            if not field_name:
                print(f"  - WARNING: No field definition found for key '{key}'. Skipping.")
                continue
                
            field_id = all_fields_map.get(field_name)

            if not field_id:
                print(f"  - WARNING: Could not find a field named '{field_name}' (key: '{key}'). Skipping.")
                continue
            
            payload = {
                 "fieldset_id": fieldset_id
            }

            print(f"  - Associating field '{field_name}' (ID: {field_id}) to fieldset '{fs_name}'...")
            response = make_api_request(
                "POST",
                f"{SNIPE_URL}/api/v1/fields/{field_id}/associate",
                json=payload
            )
            
            # Check response for THIS specific association
            if response and response.ok:
                print("    ✓ Successfully associated.")
            else:
                # Handle "already associated" gracefully
                try:
                    data = response.json() if response else {"messages": "No response"}
                    msg = str(data).lower()
                    if response and response.status_code in (409, 422) and ("already" in msg or "exists" in msg):
                        print("    → Already associated. Skipping.")
                    else:
                        print(f"    ✗ Failed to associate: {data}")
                except Exception as e:
                    print(f"    ✗ Failed to associate: {e}")

    print("\nField association process complete.")

def create_status_labels():
    """Creates status labels if they don't already exist."""
    print("\n--- Creating Status Labels ---")
    existing_labels = set(get_status_labels_map().keys())

    for label_name, config in STATUS_LABELS.items():
        if label_name in existing_labels:
            print(f"Status label '{label_name}' already exists. Skipping.") 
            continue
        print(f"Creating status label: {label_name}...")
        payload = {
            "name": label_name,
            "color": config.get("color", "#FFFFFF"),
            "type": config.get("type", "deployable"),
            "show_in_nav": config.get("show_in_nav", False),
            "default_label": config.get("default_label", False)
        }
        make_api_request("POST", f"{SNIPE_URL}/api/v1/statuslabels", json=payload)
    print("Status label creation process complete.")

def create_categories():
    """Creates categories if they don't already exist."""
    print("\n--- Creating Categories ---")
    existing_categories = set(get_categories_map().keys())

    for category_name, config in CATEGORIES.items():
        if category_name in existing_categories:
            print(f"Category '{category_name}' already exists. Skipping.") 
            continue
        print(f"Creating category: {category_name}...")
        payload = {
            "name": category_name,
            "category_type": config.get("category_type", "asset"),
            "use_default_eula": config.get("use_default_eula", False),
            "require_acceptance": config.get("require_acceptance", False),
            "checkin_email": config.get("checkin_email", False)
        }
        make_api_request("POST", f"{SNIPE_URL}/api/v1/categories", json=payload)
    print("Category creation process complete.")

def create_models():
    """Creates generic models if they don't already exist."""
    print("\n--- Creating Generic Models ---")
    existing_models = set(get_models_map().keys())
    manufacturers_map = get_manufacturers_map()
    categories_map = get_categories_map()

    for model in MODELS:
        model_name = model['name']
        if model_name in existing_models:
            print(f"Model '{model_name}' already exists. Skipping.") 
            continue
        manu_id = manufacturers_map.get(model['manufacturer'])
        cat_id = categories_map.get(model['category'])
        if not manu_id:
            print(f"  ✗ Manufacturer '{model['manufacturer']}' not found for model '{model_name}'. Skipping.")
            continue
        if not cat_id:
            print(f"  ✗ Category '{model['category']}' not found for model '{model_name}'. Skipping.")
            continue
        
        payload = {
            'name': model_name,
            'manufacturer_id': manu_id,
            'category_id': cat_id,
            'model_number': model_name.replace(' ', '-').upper()
        }
        
        print(f"Creating model: {model_name}...")
        make_api_request("POST", f"{SNIPE_URL}/api/v1/models", json=payload)
    print("Model creation process complete.")

def create_manufacturers():
    """Creates manufacturers if they don't already exist."""
    print("\n--- Creating Manufacturers ---")
    existing_manufacturers = set(get_manufacturers_map().keys())
    for manu in MANUFACTURERS:
        manu_name = manu['name']
        if manu_name in existing_manufacturers:
            print(f"Manufacturer '{manu_name}' already exists. Skipping.") 
            continue
        print(f"Creating manufacturer: {manu_name}...")
        make_api_request("POST", f"{SNIPE_URL}/api/v1/manufacturers", json=manu)
    print("Manufacturer creation process complete.")
        
def create_locations():
    """Creates locations if they don't already exist."""
    print("\n--- Creating Locations ---")
    existing_locations = set(get_location_map().keys())
    for location_name in LOCATIONS:
        if location_name in existing_locations:
            print(f"Location '{location_name}' already exists. Skipping.") 
            continue
        print(f"Creating location: {location_name}...")
        payload = {
            "name": location_name,
        }
        make_api_request("POST", f"{SNIPE_URL}/api/v1/locations", json=payload)
    print("Location creation process complete.")

# Optional: Functions to delete all created
def delete_all_fields():
    """Deletes all custom fields defined in CUSTOM FIELDS."""
    print("--- Deleting Custom Fields ---")
    existing_fields = get_allfields_map()
    for field_def in CUSTOM_FIELDS.values():
        field_name = field_def["name"]
        if field_name not in existing_fields:
            print(f"Field '{field_name}' does not exist. Skipping.")
            continue
        field_id = existing_fields[field_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/fields/{field_id}")
        print(f"Deleted field: {field_name} (ID: {field_id})")          
            
def delete_all_fieldsets():
    """Deletes all fieldsets defined in CUSTOM FIELDSETS."""
    print("\n--- Deleting Fieldsets ---")
    existing_fieldsets = get_allfieldsets_map()
    
    if not existing_fieldsets:
        print("No fieldsets found on server.")
        return
    
    for fieldset_name in CUSTOM_FIELDSETS.keys():
        if fieldset_name not in existing_fieldsets:
            print(f"Fieldset '{fieldset_name}' does not exist. Skipping.")
            continue
        fieldset_id = existing_fieldsets[fieldset_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/fieldsets/{fieldset_id}")
        print(f"Deleted fieldset: {fieldset_name} (ID: {fieldset_id})")

def delete_all_status_labels():
    """Deletes all status labels defined in STATUS_LABELS."""
    print("\n--- Deleting Status Labels ---")
    existing_labels = get_status_labels_map()
    for label_name in STATUS_LABELS.keys():
        if label_name not in existing_labels:
            print(f"Status label '{label_name}' does not exist. Skipping.")
            continue
        label_id = existing_labels[label_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/statuslabels/{label_id}")
        print(f"Deleted status label: {label_name} (ID: {label_id})")
        
def delete_all_categories():
    """Deletes all categories defined in CATEGORIES."""
    print("\n--- Deleting Categories ---")
    existing_categories = get_categories_map()
    for category_name in CATEGORIES.keys():
        if category_name not in existing_categories:
            print(f"Category '{category_name}' does not exist. Skipping.")
            continue
        category_id = existing_categories[category_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/categories/{category_id}")
        print(f"Deleted category: {category_name} (ID: {category_id})")

def delete_all_models():
    """Deletes all generic models defined in MODELS."""
    print("\n--- Deleting Generic Models ---")
    existing_models = get_models_map()
    for model in MODELS:
        model_name = model['name']
        if model_name not in existing_models:
            print(f"Model '{model_name}' does not exist. Skipping.")
            continue
        model_id = existing_models[model_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/models/{model_id}")
        print(f"Deleted model: {model_name} (ID: {model_id})")

def delete_all_manufacturers():
    """Deletes all manufacturers defined in MANUFACTURERS."""
    print("\n--- Deleting Manufacturers ---")
    existing_manufacturers = get_manufacturers_map()
    for manu in MANUFACTURERS:
        manu_name = manu['name']
        if manu_name not in existing_manufacturers:
            print(f"Manufacturer '{manu_name}' does not exist. Skipping.")
            continue
        manu_id = existing_manufacturers[manu_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/manufacturers/{manu_id}")
        print(f"Deleted manufacturer: {manu_name} (ID: {manu_id})")
                
def delete_all_locations():
    """Deletes all locations defined in LOCATIONS."""
    print("\n--- Deleting Locations ---")
    existing_locations = get_location_map()
    for location_name in LOCATIONS:
        if location_name not in existing_locations:
            print(f"Location '{location_name}' does not exist. Skipping.")
            continue
        location_id = existing_locations[location_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/locations/{location_id}")
        print(f"Deleted location: {location_name} (ID: {location_id})")

if __name__ == "__main__":
    """DELETE ALL"""
    delete_all_fields()
    delete_all_fieldsets()
    delete_all_status_labels()
    delete_all_categories()
    delete_all_manufacturers()
    delete_all_models()
    delete_all_locations()
    
    """CREATE ALL"""
    create_status_labels()
    create_categories()
    create_locations()
    create_manufacturers()
    create_models()
    create_all_fields()
    create_all_fieldsets()
    associate_fields_to_fieldsets()
    
   