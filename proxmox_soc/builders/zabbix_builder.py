"""
Zabbix Payload Builder Module
"""

from typing import Dict, Any, Optional

from proxmox_soc.builders.base_builder import BasePayloadBuilder, BuildResult
from proxmox_soc.states.base_state import StateResult


class ZabbixPayloadBuilder(BasePayloadBuilder):
    """
    Transforms canonical asset data into Zabbix Host JSON-RPC payloads.
    """
    
    GROUP_MAPPING = {
        "switch": "Network/Switches",
        "router": "Network/Routers",
        "firewall": "Network/Firewalls",
        "server": "Servers",
        "printer": "Printers",
        "camera": "IoT/Cameras",
        "desktop": "Workstations",
        "laptop": "Workstations"
    }

    def build(self, asset_data: Dict, state_result: StateResult) -> BuildResult:
        """Build Zabbix host payload from canonical data."""
        
        hostname = (asset_data.get("name") or "Unknown").strip()
        ip = asset_data.get("last_seen_ip", "")
        
        # Technical Name: clean spaces/slashes
        zabbix_host = hostname.replace(" ", "_").replace("/", "-")
        
        # Determine group
        device_type = asset_data.get("device_type", "")
        group_name = self.get_group_name(device_type)
        
        payload = {
            "host": zabbix_host,
            "name": hostname,
            "groups": [{"name": group_name}],  # Will be resolved to ID by dispatcher
            "interfaces": [{
                "type": 1,
                "main": 1,
                "useip": 1,
                "ip": ip,
                "dns": "",
                "port": "10050"
            }],
            "inventory_mode": 1,
            "inventory": {
                "asset_tag": asset_data.get("asset_tag") or "",
                "serialno_a": asset_data.get("serial") or "",
                "macaddress_a": asset_data.get("mac_addresses") or "",
                "vendor": asset_data.get("manufacturer") or "",
                "model": asset_data.get("model") or "",
            },
            "tags": [
                {"tag": "source", "value": asset_data.get("_source", "hydra")},
                {"tag": "device_type", "value": device_type or "unknown"}
            ]
        }
        
        return BuildResult(
            payload=payload,
            asset_id=state_result.asset_id,
            action=state_result.action,
            metadata={
                "group_name": group_name,
                "source": asset_data.get("_source")
            }
        )

    def get_group_name(self, device_type: str) -> str:
        """Determine target host group name based on device type."""
        dt = (device_type or "").lower()
        for key, group in self.GROUP_MAPPING.items():
            if key in dt:
                return group
        return "Discovered hosts"