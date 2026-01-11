from typing import Dict
from proxmox_soc.states.base_state import BaseStateManager, StateResult
from proxmox_soc.asset_engine.asset_finder import AssetFinder
from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService
from proxmox_soc.config.network_config import STATIC_IP_MAP

class SnipeStateManager(BaseStateManager):
    def __init__(self):
        self.service = AssetService()
        self.finder = AssetFinder(self.service)

    def check(self, asset_data: Dict) -> StateResult:
        existing = self.find_existing_asset(asset_data)
        if existing:
            return StateResult(
                action='update',
                asset_id=existing['id'], # Snipe ID
                existing=existing
            )
            
        if self._has_sufficient_data(asset_data):
            return StateResult(action='create', asset_id=None, existing=None)

        return StateResult(action='skip', asset_id=None, existing=None)

    def find_existing_asset(self, asset_data: Dict) -> Optional[Dict]:
        """Find existing asset using prioritized matching strategies."""
        return (
            self.finder.by_serial(asset_data.get('serial')) or
            self.finder.by_asset_tag(asset_data.get('asset_tag')) or
            self.finder.by_static_mapping(asset_data.get('last_seen_ip')) or
            self.finder.by_mac_address(asset_data) or
            self.finder.by_hostname(asset_data) or
            self.finder.by_ip_address(asset_data.get('last_seen_ip')) or
            self.finder.by_fallback_identifiers(asset_data)
        )
        
    def _has_sufficient_data(self, asset_data: Dict) -> bool:
        """Check if asset has enough data to create a new record."""
        if asset_data.get('last_seen_ip') in STATIC_IP_MAP:
            return True
        if asset_data.get('serial'):
            return True
        if any(asset_data.get(k) for k in ('mac_addresses', 'wifi_mac', 'ethernet_mac')):
            return True
        if asset_data.get('asset_tag'):
            return True
        if asset_data.get('intune_device_id') or asset_data.get('azure_ad_id'):
            return True
        
        name = (asset_data.get('name') or '').strip()
        dns = asset_data.get('dns_hostname', '')
        if name and not name.lower().startswith('device-') and dns not in ('', '_gateway'):
            return True
        
        return False

    def record(self, asset_id, asset_data, action):
        pass # Snipe API handles its own persistence