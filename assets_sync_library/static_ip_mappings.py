"""
Static IP Address Mapping
This is the highest priority mapping. If an asset's IP is found here,
these values will be used for categorization and naming.

Format: 'IP_ADDRESS': {'device_type': '...', 'category': '...', 'name': '...', 'location': '...', 'placement': '...'}

device_type: Helps the categorizer select the right logic (e.g., 'Switch', 'Printer', 'Server').
category:    The final Snipe-IT category for the asset.
name:        The desired name for the asset in Snipe-IT.
location:    The physical location name as defined in Snipe-IT.
placement:   Specific placement information (e.g., Rack U23, Room 101).
"""

STATIC_IP_MAP = {
    # --- Glostrup Location ---
    '192.168.1.1': {'device_type': 'Firewall', 'category': 'Firewalls', 'name': 'Meraki MX85 Gateway', 'location': 'Glostrup Office - Home', 'placement': 'Main Rack U10'},
    '192.168.2.1': {'device_type': 'Firewall', 'category': 'Firewalls', 'name': 'Meraki MX85 DMZ Gateway', 'location': 'Glostrup Office - Home', 'placement': 'Main Rack U11'},
    '192.168.1.2': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Core switch Aruba 2930', 'location': 'Glostrup Office - Home', 'placement': 'Main Rack U12'},
    '192.168.1.9': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Server switch HP 1910-24G', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U5'},
    '192.168.1.10': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch HP 1920-24G - 1', 'location': 'Glostrup Office - Home', 'placement': 'Patch Panel A'},
    '192.168.1.11': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch HP 1920-24G - 2', 'location': 'Glostrup Office - Home', 'placement': 'Patch Panel B'},
    '192.168.1.12': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch HP 1920-24G POE', 'location': 'Glostrup Office - Home', 'placement': 'Patch Panel C'},
    '192.168.1.13': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch HP 1920-24G POE (2)', 'location': 'Glostrup Office - Home', 'placement': 'Patch Panel D'},
    '192.168.1.14': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch HP 1920-24G - 3', 'location': 'Glostrup Office - Home', 'placement': 'Patch Panel E'},
    '192.168.1.15': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch HP 1920-24G - 4', 'location': 'Glostrup Office - Home', 'placement': 'Patch Panel F'},
    '192.168.1.20': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch HP 1920-48G POE', 'location': 'Glostrup Office - Home', 'placement': 'Main Rack U15'},
    '192.168.1.22': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch D-Link DGS-1100-08P IT', 'location': 'Glostrup Office - Home', 'placement': 'IT Department'},
    '192.168.1.23': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch D-Link DGS-1100-08P Serverrum', 'location': 'Glostrup Office - Home', 'placement': 'Server Room'},
    '192.168.1.25': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch Unify Ubiquiti USW-24-PoE', 'location': 'Glostrup Office - Home', 'placement': 'Main Rack U16'},
    '192.168.1.26': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch Unify Ubiquiti USW-24-PoE Kantine', 'location': 'Glostrup Office - Home', 'placement': 'Canteen'},
    '192.168.1.27': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch Unify Ubiquiti USW-24-PoE Lille X felt', 'location': 'Glostrup Office - Home', 'placement': 'Area X'},
    '192.168.5.2': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch 3560', 'location': 'Glostrup Office - Home', 'placement': 'Old Lab'},
    '192.168.5.7': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch D-Link DSG 1100-08P Stuen', 'location': 'Glostrup Office - Home', 'placement': 'Ground Floor'},
    '192.168.5.8': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Switch D-Link DGS-1100-08P Bogholderiet', 'location': 'Glostrup Office - Home', 'placement': 'Accounting'},

    # Routers
    '192.168.1.30': {'device_type': 'Router', 'category': 'Routers', 'name': 'NiaNet MPLS (Reserveret)', 'location': 'Glostrup Office - Home', 'placement': 'Main Rack U1'},
    '192.168.1.31': {'device_type': 'Router', 'category': 'Routers', 'name': 'NiaNet MPLS (Reserveret 2)', 'location': 'Glostrup Office - Home', 'placement': 'Main Rack U2'},
    '192.168.1.32': {'device_type': 'Router', 'category': 'Routers', 'name': 'NiaNet MPLS (Reserveret 3)', 'location': 'Glostrup Office - Home', 'placement': 'Main Rack U3'},

    # Printers
    '192.168.1.42': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Printer C4510 Reception', 'location': 'Glostrup Office - Home', 'placement': 'Reception Desk'},
    '192.168.1.43': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Printer C4510 Foran Krogh', 'location': 'Glostrup Office - Home', 'placement': 'Hallway'},
    '192.168.1.45': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Printer ZD421 Test', 'location': 'Glostrup Office - Home', 'placement': 'Test Lab'},

    # Servers & Appliances
    '192.168.1.170': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'name': 'Vcenter01', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx06'},
    '192.168.1.171': {'device_type': 'Server', 'category': 'Servers', 'name': 'IMM 1', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U20'},
    '192.168.1.172': {'device_type': 'Server', 'category': 'Servers', 'name': 'IMM 2', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U21'},
    '192.168.1.173': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'name': 'Esx06', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U22'},
    '192.168.1.174': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'name': 'Esx07', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U23'},
    '192.168.1.181': {'device_type': 'Server', 'category': 'Servers', 'name': 'DC03', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx04'},
    '192.168.1.186': {'device_type': 'Server', 'category': 'Servers', 'name': 'Filesrvr04', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx05'},
    '192.168.1.196': {'device_type': 'Server', 'category': 'Servers', 'name': 'IMM 3', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U24'},
    '192.168.1.197': {'device_type': 'Server', 'category': 'Servers', 'name': 'IMM 4', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U25'},
    '192.168.1.198': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'name': 'Esx04', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U26'},
    '192.168.1.199': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'name': 'Esx05', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U27'},
    '192.168.1.222': {'device_type': 'Server', 'category': 'Servers', 'name': 'Visma01', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx07'},
    '192.168.1.228': {'device_type': 'Server', 'category': 'Servers', 'name': 'Consult05', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx06'},
    '192.168.1.229': {'device_type': 'Server', 'category': 'Servers', 'name': 'DC02', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx04'},
    '192.168.1.230': {'device_type': 'Server', 'category': 'Servers', 'name': 'Terminal02', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx05'},
    '192.168.1.232': {'device_type': 'Server', 'category': 'Servers', 'name': 'Veeam01', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx07'},
    '192.168.1.234': {'device_type': 'Server', 'category': 'Servers', 'name': 'Filesrvr03', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx06'},
    '192.168.1.235': {'device_type': 'Server', 'category': 'Servers', 'name': 'Scribe01', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx04'},
    '192.168.1.236': {'device_type': 'Server', 'category': 'Servers', 'name': 'Consult06', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx05'},
    '192.168.1.237': {'device_type': 'Server', 'category': 'Servers', 'name': 'Netmonitor', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx07'},
    '192.168.1.239': {'device_type': 'Server', 'category': 'Servers', 'name': 'Consult04', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx06'},
    '192.168.1.240': {'device_type': 'Server', 'category': 'Servers', 'name': 'Consult07', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx04'},
    '192.168.1.242': {'device_type': 'Server', 'category': 'Servers', 'name': 'Fotostation01', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx05'},
    '192.168.1.244': {'device_type': 'Server', 'category': 'Servers', 'name': 'Visma05 (TEST)', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx07'},
    '192.168.1.246': {'device_type': 'Server', 'category': 'Servers', 'name': 'Backup02', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx06'},
    '192.168.1.247': {'device_type': 'Server', 'category': 'Virtual Machines (On-Premises)', 'name': 'APC Powerchute vApp', 'location': 'Glostrup Office - Home', 'placement': 'VM on Esx04'},
    '192.168.2.15': {'device_type': 'Server', 'category': 'Servers', 'name': 'IntergrationPROD', 'location': 'Glostrup Office - Home', 'placement': 'DMZ'},
    '192.168.2.20': {'device_type': 'Server', 'category': 'Servers', 'name': 'IntergrationTEST', 'location': 'Glostrup Office - Home', 'placement': 'DMZ'},

    # Storage Devices
    '192.168.1.185': {'device_type': 'Storage Device', 'category': 'Storage Devices', 'name': 'BackupNAS02 Synology RS815RP+', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U30'},
    '192.168.1.226': {'device_type': 'Storage Device', 'category': 'Storage Devices', 'name': 'Synology NAS', 'location': 'Glostrup Office - Home', 'placement': 'Server Room Corner'},
    '192.168.1.251': {'device_type': 'Storage Device', 'category': 'Storage Devices', 'name': 'BackupNAS03 Synology RS820RP+', 'location': 'Glostrup Office - Home', 'placement': 'Server Rack U31'},

    # --- Odense Location ---
    '192.168.200.1': {'device_type': 'Router', 'category': 'Routers', 'name': 'Odense MPLS Gateway', 'location': 'Odense Office', 'placement': 'Main Rack U1'},
    '192.168.200.3': {'device_type': 'Router', 'category': 'Routers', 'name': 'Odense NiaNet MPLS (Reserveret)', 'location': 'Odense Office', 'placement': 'Main Rack U2'},
    '192.168.200.4': {'device_type': 'Router', 'category': 'Routers', 'name': 'Odense NiaNet MPLS (Reserveret 2)', 'location': 'Odense Office', 'placement': 'Main Rack U3'},
    '192.168.200.5': {'device_type': 'Router', 'category': 'Routers', 'name': 'Odense NiaNet MPLS (Reserveret 3)', 'location': 'Odense Office', 'placement': 'Main Rack U4'},
    '192.168.200.10': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Odense Switch HP 1910-24 POE', 'location': 'Odense Office', 'placement': 'Main Rack U10'},
    '192.168.200.11': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Odense Switch D-Link DGS-1100-08P Logistik', 'location': 'Odense Office', 'placement': 'Logistics Area'},
    '192.168.200.12': {'device_type': 'Switch', 'category': 'Switches', 'name': 'Odense Switch D-Link DGS-1100-08P Skrabelod', 'location': 'Odense Office', 'placement': 'Scratch-off Area'},
    '192.168.200.15': {'device_type': 'Storage Device', 'category': 'Storage Devices', 'name': 'BackupNAS04-Ode', 'location': 'Odense Office', 'placement': 'Server Closet'},
    '192.168.200.201': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Odense Printer Ricoh IM C300', 'location': 'Odense Office', 'placement': 'Main Office Area'},
    '192.168.200.206': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Odense Printer Ricoh c5100', 'location': 'Odense Office', 'placement': 'Production Floor'},
    '192.168.200.207': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Odense Printer Ricoh Ferry', 'location': 'Odense Office', 'placement': 'Shipping Dept'},
    '192.168.200.208': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Odense Printer HP LaserJet Pro M402dw', 'location': 'Odense Office', 'placement': 'Front Office'},
    '192.168.200.209': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Odense Printer Ricoh SP 4520DN', 'location': 'Odense Office', 'placement': 'Warehouse'},
    '192.168.200.210': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Odense Label Printer Zebra GK420D', 'location': 'Odense Office', 'placement': 'Packing Station 1'},
    '192.168.200.211': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Odense Printer HP Pagewide 477DW', 'location': 'Odense Office', 'placement': 'Marketing Dept'},
    '192.168.200.212': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Odense Label Printer Zebra ZD421', 'location': 'Odense Office', 'placement': 'Packing Station 2'},
    '192.168.200.213': {'device_type': 'Printer', 'category': 'Printers', 'name': 'Odense Fakturaprinter Brother HL-L6415DN', 'location': 'Odense Office', 'placement': 'Finance Dept'},
}
