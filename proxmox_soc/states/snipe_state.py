"""
Snipe-IT State Manager
Handles asset existence checks against Snipe-IT API.
"""

from typing import Dict, Optional

from proxmox_soc.states.base_state import BaseStateManager, StateResult
from proxmox_soc.asset_engine.asset_finder import AssetFinder
from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService
from proxmox_soc.config.network_config import STATIC_IP_MAP


class SnipeStateManager(BaseStateManager):
    """
    Manages asset state against Snipe-IT.
    
    Uses AssetFinder to locate existing assets via multiple strategies.
    """
    
    IDENTITY_PRIORITY = ('serial', 'asset_tag', 'mac_addresses', 'intune_device_id')
    
    def __init__(self):
        self.service = AssetService()
        self.finder = AssetFinder(self.service)
        self._cache: Dict[str, Dict] = {}

    def generate_id(self, asset_data: Dict) -> Optional[str]:
        """Generate unique identifier from asset data."""
        for field in self.IDENTITY_PRIORITY:
            value = asset_data.get(field)
            if value:
                return f"snipe:{field}:{value}"
        return None

    def check(self, asset_data: Dict) -> StateResult:
        """Check if asset exists in Snipe-IT and determine action."""
        asset_id = self.generate_id(asset_data)
        existing = self._find_existing(asset_data)
        
        if existing:
            return StateResult(
                action='update',
                asset_id=str(existing['id']),  # Use Snipe ID as asset_id
                existing=existing,
                reason=f"Found existing Snipe-IT asset ID: {existing['id']}"
            )
            
        if self._has_sufficient_data(asset_data):
            return StateResult(
                action='create',
                asset_id=asset_id or '',
                existing=None,
                reason='New asset with sufficient data'
            )

        return StateResult(
            action='skip',
            asset_id=asset_id or '',
            existing=None,
            reason='Insufficient data for creation'
        )

    def record(self, asset_id: str, asset_data: Dict, action: str) -> None:
        """Cache the result (Snipe-IT API handles persistence)."""
        self._cache[asset_id] = {
            'action': action,
            'name': asset_data.get('name'),
        }

    def _find_existing(self, asset_data: Dict) -> Optional[Dict]:
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