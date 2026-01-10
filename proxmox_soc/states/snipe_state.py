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
        # 1. Logic: Find Existing (Moved from AssetMatcher)
        existing = (
            self.finder.by_serial(asset_data.get('serial')) or
            self.finder.by_asset_tag(asset_data.get('asset_tag')) or
            self.finder.by_static_mapping(asset_data.get('last_seen_ip')) or
            self.finder.by_mac_address(asset_data) or
            self.finder.by_hostname(asset_data) or
            self.finder.by_ip_address(asset_data.get('last_seen_ip')) or
            self.finder.by_fallback_identifiers(asset_data)
        )

        if existing:
            return StateResult(
                action='update',
                asset_id=existing['id'], # Snipe ID
                existing=existing
            )

        # 2. Logic: Check Viability (Moved from AssetMatcher)
        if self._has_sufficient_data(asset_data):
            return StateResult(action='create', asset_id=None, existing=None)

        return StateResult(action='skip', asset_id=None, existing=None)

    def _has_sufficient_data(self, asset_data: Dict) -> bool:
        """Exact copy of your previous logic"""
        if asset_data.get('last_seen_ip') in STATIC_IP_MAP: return True
        if asset_data.get('serial'): return True
        # ... (paste the rest of your logic here) ...
        return False

    def record(self, asset_id, asset_data, action):
        pass # Snipe API handles its own persistence