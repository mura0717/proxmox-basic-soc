"""
Static IP Address Mapping
This is the highest priority mapping. If an asset's IP is found here,
these values will be used for categorization and naming.

Format: 'IP_ADDRESS': {'device_type': '...', 'category': '...', 'host_name': '...', 'services': '...', location': '...', 'placement': '...'}

device_type: Helps the categorizer select the right logic (e.g., 'Switch', 'Printer', 'Server').
category:    The final Snipe-IT category for the asset.
host_name:   The desired host_name for the asset in Snipe-IT.
services:    Services present on the host machine.
location:    The physical location host_name as defined in Snipe-IT.
placement:   Specific placement information (e.g., Rack U23, Room 101).
"""

STATIC_IP_MAP = {
    # --- Glostrup Location ---
    '192.168.1.1': {'device_type': 'Firewall', 'category': 'Firewalls', 'host_name': 'Meraki MX85 Gateway', 'services': 'default gateway', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.2.1': {'device_type': 'Firewall', 'category': 'Firewalls', 'host_name': 'Meraki MX85 DMZ Gateway', 'services': '', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.2': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Core switch Aruba 2930', 'services': '', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.9': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Server switch HP 1910-24G', 'services': 'HP 1910-24G', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.10': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch HP 1920-24G - 1', 'services': 'HP 1920-24G - 1', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.11': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch HP 1920-24G - 2', 'services': 'HP 1920-24G - 2', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.12': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch HP 1920-24G POE', 'services': 'HP 1920-24G POE', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.13': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch HP 1920-24G POE (2)', 'services': 'HP 1920-24G POE', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.14': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch HP 1920-24G - 3', 'services': 'HP 1920-24G - 3', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.15': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch HP 1920-24G - 4', 'services': 'HP 1920-24G - 4', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.20': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch HP 1920-48G POE', 'services': 'HP 1920-48G POE', 'location': 'Glostrup', 'placement': 'Mellem X felt'},
    '192.168.1.22': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch D-Link DGS-1100-08P IT', 'services': 'D-Link DGS-1100-08P', 'location': 'Glostrup', 'placement': 'IT Department'},
    '192.168.1.23': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch D-Link DGS-1100-08P Serverrum', 'services': 'D-Link DGS-1100-08P', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.25': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch Unify Ubiquiti USW-24-PoE', 'services': 'Unify Ubiquiti USW-24-PoEp', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.26': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch Unify Ubiquiti USW-24-PoE Kantine', 'services': 'Unify Ubiquiti USW-24-PoE', 'location': 'Glostrup', 'placement': 'Canteen'},
    '192.168.1.27': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch Unify Ubiquiti USW-24-PoE Lille X felt', 'services': 'Unify Ubiquiti USW-24-PoEp', 'location': 'Glostrup', 'placement': 'Lille X felt'},
    '192.168.4.1': {'device_type': 'Firewall', 'category': 'Firewalls', 'host_name': 'Gateway', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.5.2': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch 3560', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.5.7': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch D-Link DSG 1100-08P', 'services': '', 'location': 'Glostrup', 'placement': 'Consultation Room'},
    '192.168.5.8': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch D-Link DGS-1100-08P', 'services': '', 'location': 'Glostrup', 'placement': 'Accounting'},

    # Routers
    '192.168.1.30': {'device_type': 'Router', 'category': 'Routers', 'host_name': 'NiaNet MPLS (Reserved 1)', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.31': {'device_type': 'Router', 'category': 'Routers', 'host_name': 'NiaNet MPLS (Reserved 2)', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.32': {'device_type': 'Router', 'category': 'Routers', 'host_name': 'NiaNet MPLS (Reserved 3)', 'services': '', 'location': 'Glostrup', 'placement': ''},

    # Printers
    '192.168.1.42': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'Printer C4510', 'services': '', 'location': 'Glostrup', 'placement': 'Reception Desk'},
    '192.168.1.43': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'Printer C4510', 'services': '', 'location': 'Glostrup', 'placement': 'Hallway - Foran Krogh'},
    '192.168.1.45': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'Printer ZD421 Test', 'services': '', 'location': 'Glostrup', 'placement': 'Test - will be moved to Odense'},

    # Servers & Appliances
    '192.168.1.170': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'host_name': 'Vcenter01', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.171': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'IMM 1', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.172': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'IMM 2', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.173': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'host_name': 'Esx06', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.174': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'host_name': 'Esx07', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.181': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'DC03', 'services': '', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.186': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Filesrvr04', 'services': '', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.196': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'IMM 3', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.197': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'IMM 4', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.198': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'host_name': 'Esx04', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.199': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'host_name': 'Esx05', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.222': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Visma01', 'services': 'sql', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.228': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Consult05', 'services': '', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.229': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'DC02', 'services': '', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.230': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Terminal02', 'services': 'rdp', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.232': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Veeam01', 'services': 'veeam backup(not in domain)', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.234': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Filesrvr03', 'services': 'radius', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.235': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Scribe01', 'services': '', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.236': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Consult06', 'services': '', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.237': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Netmonitor', 'services': '', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.239': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Consult04', 'services': 'print, azure ad connect, terminal radius', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.240': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Consult07', 'services': 'azure ad connect', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.242': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Fotostation01', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.244': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Visma05 (TEST)', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.246': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'Backup02', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.1.247': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'host_name': '', 'services': 'https', 'location': 'Glostrup', 'placement': ''},
    '192.168.2.15': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'IntergrationPROD', 'services': '', 'location': 'Glostrup', 'placement': ''},
    '192.168.2.20': {'device_type': 'Server', 'category': 'Servers', 'host_name': 'IntergrationTEST', 'services': '', 'location': 'Glostrup', 'placement': ''},

    # Storage Devices
    '192.168.1.185': {'device_type': 'Storage Device', 'category': 'Storage Devices', 'host_name': 'BackupNAS02 Synology RS815RP+', 'services': '', 'location': 'Glostrup', 'placement': '3. floor X felt'},
    '192.168.1.226': {'device_type': 'Storage Device', 'category': 'Storage Devices', 'host_name': 'Synology NAS', 'services': '', 'location': 'Glostrup', 'placement': 'Server Room'},
    '192.168.1.251': {'device_type': 'Storage Device', 'category': 'Storage Devices', 'host_name': 'BackupNAS03 Synology RS820RP+', 'services': '', 'location': 'Glostrup', 'placement': ''},

    # --- Odense Location ---
    '192.168.200.1': {'device_type': 'Router', 'category': 'Routers', 'host_name': 'MPLS Gateway', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.3': {'device_type': 'Router', 'category': 'Routers', 'host_name': 'NiaNet MPLS (Reserved 1)', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.4': {'device_type': 'Router', 'category': 'Routers', 'host_name': 'NiaNet MPLS (Reserved 2)', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.5': {'device_type': 'Router', 'category': 'Routers', 'host_name': 'NiaNet MPLS (Reserved 3)', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.10': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch HP 1910-24 POE', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.11': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch D-Link DGS-1100-08P', 'services': '', 'location': 'Odense', 'placement': 'Logistics Area - forsendelse'},
    '192.168.200.12': {'device_type': 'Switch', 'category': 'Switches', 'host_name': 'Switch D-Link DGS-1100-08P', 'services': '', 'location': 'Odense', 'placement': 'Logistics - Skrabelod'},
    '192.168.200.15': {'device_type': 'Storage Device', 'category': 'Storage Devices', 'host_name': 'BackupNAS04-Ode', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.201': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'Ricoh IM C300', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.206': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'Ricoh c5100', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.207': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'Ricoh Ferry', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.208': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'HP LaserJet Pro M402dw', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.209': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'Ricoh SP 4520DN', 'services': '', 'location': 'Odense', 'placement': ''},
    '192.168.200.210': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'Zebra GK420D', 'services': 'Label Printer', 'location': 'Odense', 'placement': ''},
    '192.168.200.211': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'HP Pagewide 477DW', 'services': '', 'location': 'Odense', 'placement': 'Logistics - 1. floor'},
    '192.168.200.212': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'Zebra ZD421', 'services': 'Label Printer ', 'location': 'Odense', 'placement': ''},
    '192.168.200.213': {'device_type': 'Printer', 'category': 'Printers', 'host_name': 'Brother HL-L6415DN', 'services': 'Fakturaprinter', 'location': 'Odense', 'placement': ''},
}
