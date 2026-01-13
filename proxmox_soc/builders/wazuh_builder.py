"""
Wazuh Payload Builder Module
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

from proxmox_soc.builders.base_builder import BasePayloadBuilder, BuildResult
from proxmox_soc.states.base_state import StateResult


class WazuhPayloadBuilder(BasePayloadBuilder):
    """
    Transforms canonical asset data into Wazuh Log Events.
    """
    
    VLAN_MAPPING = {
        "192.168.1.": "Primary LAN",
        "192.168.2.": "DMZ",
        "192.168.200.": "Odense Office",
        "172.20.20.": "Guest WiFi",
        "10.255.255.": "Security Cameras",
    }
    EXTENDED_PREFIXES = ("192.168.4.", "192.168.5.", "192.168.6.", "192.168.7.")

    def build(self, asset_data: Dict, state_result: StateResult) -> BuildResult:
        """Build Wazuh log event from canonical data."""
        
        ports = asset_data.get("nmap_open_ports", [])
        if isinstance(ports, str):
            ports = [p.strip() for p in ports.split('\n') if p.strip()]

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "hydra_asset_scan",
            "action": state_result.action,
            "wazuh_id": state_result.asset_id,
            "source": asset_data.get("_source"),
            "asset": {
                "name": asset_data.get("name"),
                "ip": asset_data.get("last_seen_ip"),
                "mac": asset_data.get("mac_addresses"),
                "serial": asset_data.get("serial"),
                "asset_tag": asset_data.get("asset_tag"),
            },
            "classification": {
                "manufacturer": asset_data.get("manufacturer"),
                "model": asset_data.get("model"),
                "category": asset_data.get("category"),
                "device_type": asset_data.get("device_type"),
            },
            "security": {
                "open_ports": ports,
                "os_guess": asset_data.get("nmap_os_guess"),
                "compliance": asset_data.get("intune_compliance"),
                "vlan": self._get_vlan(asset_data.get("last_seen_ip"))
            }
        }
        
        return BuildResult(
            payload=event,
            asset_id=state_result.asset_id,
            action=state_result.action,
            metadata={"source": asset_data.get("_source")}
        )

    def _get_vlan(self, ip: str) -> Optional[str]:
        if not ip:
            return None
        for prefix, vlan in self.VLAN_MAPPING.items():
            if ip.startswith(prefix):
                return vlan
        if ip.startswith(self.EXTENDED_PREFIXES):
            return "Extended"
        return "Unknown"