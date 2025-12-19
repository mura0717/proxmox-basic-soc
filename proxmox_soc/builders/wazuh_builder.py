"""
Wazuh Payload Builder Module
"""

from datetime import datetime, timezone
from typing import Dict, Any, Optional

class WazuhPayloadBuilder:
    """
    Transforms canonical asset data into Wazuh Log Events.
    Pure logic.
    """

    def build_event(self, asset: Dict[str, Any]) -> Dict:
        """Transforms canonical asset data into Wazuh Log Event."""
        data = asset.get("canonical_data", {})
        payload = asset.get("snipe_payload", {})
        
        # Extract open ports
        ports = data.get("open_ports", [])
        if isinstance(ports, str):
            ports = [p.strip() for p in ports.split('\n') if p.strip()]

        return {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": "hydra_asset_scan",
            "action": asset.get("action"),
            "source": data.get("_source"),
            "asset": {
                "name": payload.get("name") or data.get("name"),
                "ip": data.get("last_seen_ip"),
                "mac": data.get("mac_addresses"),
                "serial": data.get("serial"),
                "asset_tag": asset.get("asset_tag"),
            },
            "classification": {
                "manufacturer": data.get("manufacturer"),
                "model": data.get("model"),
                "category": data.get("category"),
                "device_type": data.get("device_type"),
            },
            "snipe_id": asset.get("snipe_id"),
            "security": {
                "open_ports": ports,
                "vlan": self._get_vlan(data.get("last_seen_ip"))
            }
        }

    def _get_vlan(self, ip: str) -> Optional[str]:
        if not ip: return None
        if ip.startswith("192.168.1."): return "Primary LAN"
        if ip.startswith("192.168.2."): return "DMZ"
        if ip.startswith("192.168.200."): return "Odense Office"
        if ip.startswith(("192.168.4.", "192.168.5.", "192.168.6.", "192.168.7.")): return "Clients"
        if ip.startswith("172.20.20."): return "Guest WiFi"
        if ip.startswith("10.255.255."): return "Security Cameras"
        return "Unknown"