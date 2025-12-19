"""
Zabbix Payload Builder Module
"""

from typing import Dict, Any

class ZabbixPayloadBuilder:
    """
    Transforms canonical asset data into Zabbix Host JSON-RPC payloads.
    Pure logic: no API calls.
    """

    def build_host(self, asset: Dict[str, Any], group_id: str) -> Dict:
        """Transforms canonical asset data into Zabbix Host Payload."""
        data = asset.get("canonical_data", {})
        payload = asset.get("snipe_payload", {})
        
        hostname = payload.get("name") or data.get("host_name") or data.get("name")
        ip = data.get("last_seen_ip")
        
        # Technical Name (Host key): clean spaces
        zabbix_host = hostname.replace(" ", "_").replace("/", "-")
        
        return {
            "host": zabbix_host,
            "name": hostname, # Visible name
            "groups": [{"groupid": group_id}],
            "interfaces": [{
                "type": 1, "main": 1, "useip": 1,
                "ip": ip, "dns": "", "port": "10050"
            }],
            "inventory_mode": 1, # Automatic
            "inventory": {
                "asset_tag": data.get("asset_tag") or "",
                "serialno_a": data.get("serial") or "",
                "macaddress_a": data.get("mac_addresses") or "",
                "vendor": data.get("manufacturer") or "",
                "model": data.get("model") or "",
                "notes": f"Snipe-IT ID: {asset.get('snipe_id')}"
            },
            "tags": [
                {"tag": "source", "value": data.get("_source", "hydra")},
                {"tag": "device_type", "value": data.get("device_type", "unknown")}
            ]
        }

    def get_group_name(self, device_type: str) -> str:
        """Determines target host group name based on device type."""
        dt = (device_type or "").lower()
        mapping = {
            "switch": "Network/Switches",
            "router": "Network/Routers",
            "firewall": "Network/Firewalls",
            "server": "Servers",
            "printer": "Printers",
            "camera": "IoT/Cameras",
            "desktop": "Workstations",
            "laptop": "Workstations"
        }
        for key, group in mapping.items():
            if key in dt: return group
        return "Discovered hosts"