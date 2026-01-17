"""
Snipe-IT State Manager
Handles asset existence checks against Snipe-IT API with caching.
"""

import os
from typing import Dict, Optional, List

from proxmox_soc.states.base_state import BaseStateManager, StateResult
from proxmox_soc.asset_engine.asset_finder import AssetFinder
from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService
from proxmox_soc.config.network_config import STATIC_IP_MAP
from proxmox_soc.utils.mac_utils import normalize_mac_semicolon, get_primary_mac_address


class SnipeStateManager(BaseStateManager):
    """
    Manages asset state against Snipe-IT with caching to avoid rate limiting.
    """
    
    IDENTITY_PRIORITY = ('serial', 'asset_tag', 'mac_addresses', 'intune_device_id')
    
    def __init__(self):
        self.service = AssetService()
        self.finder = AssetFinder(self.service)
        self._match_cache: Dict[str, Dict] = {}
        self._all_assets: Optional[List[Dict]] = None
        self._cache_loaded = False
        self.debug = os.getenv('SNIPE_STATE_DEBUG', '0') == '1'

    def _load_all_assets(self) -> None:
        """Load all assets from Snipe-IT once for matching."""
        if self._cache_loaded:
            return
            
        print("  [Snipe State] Loading all assets for matching...")
        try:
            self._all_assets = self.service.get_all() or []
            self._cache_loaded = True
            print(f"  [Snipe State] Loaded {len(self._all_assets)} existing assets")
            
            # Build lookup indexes
            self._index_by_serial = {}
            self._index_by_mac = {}
            self._index_by_asset_tag = {}
            self._index_by_name = {}
            
            for asset in self._all_assets:
                # Index by serial
                serial = asset.get('serial')
                if serial:
                    self._index_by_serial[serial.upper()] = asset
                
                # Index by asset tag
                tag = asset.get('asset_tag')
                if tag:
                    self._index_by_asset_tag[tag] = asset
                
                standard_mac = asset.get('mac_address')
                if standard_mac:
                    norm = normalize_mac_semicolon(standard_mac)
                    if norm:
                        mac_key = norm.replace(':', '').upper()
                        if mac_key not in self._index_by_mac:
                            self._index_by_mac[mac_key] = asset
                
                # Index by MAC (from custom fields)
                for cf_name, cf_data in asset.get('custom_fields', {}).items():
                    if 'mac' in cf_name.lower():
                        mac = cf_data.get('value', '') if isinstance(cf_data, dict) else cf_data
                        if mac:
                            for m in str(mac).replace(',', '\n').replace(';', '\n').split('\n'):
                                m = m.strip()
                                if not m:
                                    continue
                                norm = normalize_mac_semicolon(m)
                                if norm:
                                    mac_key = norm.replace(':', '').upper()
                                    if mac_key not in self._index_by_mac:
                                        self._index_by_mac[mac_key] = asset
                
                # Index by name
                name = asset.get('name')
                if name:
                    self._index_by_name[name.lower()] = asset
                    
        except Exception as e:
            print(f"  [Snipe State] Error loading assets: {e}")
            self._all_assets = []
            self._cache_loaded = True

    def generate_id(self, asset_data: Dict) -> Optional[str]:
        """Generate unique identifier from asset data."""
        for field in self.IDENTITY_PRIORITY:
            value = asset_data.get(field)
            if value:
                return f"snipe:{field}:{value}"
        return None

    def check(self, asset_data: Dict) -> StateResult:
        """Check if asset exists in Snipe-IT and determine action."""
        # Ensure cache is loaded
        self._load_all_assets()
        
        asset_id = self.generate_id(asset_data)
        
        # Check cache first
        cache_key = self._get_cache_key(asset_data)
        if cache_key and cache_key in self._match_cache:
            existing = self._match_cache[cache_key]
            return StateResult(
                action='update',
                asset_id=str(existing['id']),
                existing=existing,
                reason=f"Cached match: Snipe ID {existing['id']}"
            )
        
        # Find existing asset using indexes (fast, no API calls)
        existing = self._find_existing_cached(asset_data)
        
        if existing:
            # Cache the match
            if cache_key:
                self._match_cache[cache_key] = existing
            
            return StateResult(
                action='update',
                asset_id=str(existing['id']),
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

    def _get_cache_key(self, asset_data: Dict) -> Optional[str]:
        """Generate cache key from asset identifiers."""
        if asset_data.get('serial'):
            return f"serial:{asset_data['serial'].upper()}"
        if asset_data.get('mac_addresses'):
            # Take first MAC for cache key
            mac = get_primary_mac_address(asset_data['mac_addresses'])
            if mac:
                return f"mac:{mac.replace(':', '')}"
        if asset_data.get('asset_tag'):
            return f"tag:{asset_data['asset_tag']}"
        return None

    def _find_existing_cached(self, asset_data: Dict) -> Optional[Dict]:
        """Find existing asset using cached indexes (no API calls)."""
        
        # 1. By serial (most reliable)
        serial = asset_data.get('serial')
        if serial:
            match = self._index_by_serial.get(serial.upper())
            if match:
                if self.debug:
                    print(f"    Match by serial: {serial} -> ID {match['id']}")
                return match
        
        # 2. By asset tag
        tag = asset_data.get('asset_tag')
        if tag:
            match = self._index_by_asset_tag.get(tag)
            if match:
                if self.debug:
                    print(f"    Match by asset_tag: {tag} -> ID {match['id']}")
                return match
        
        # 3. By MAC address
        mac_val = asset_data.get('mac_addresses') or asset_data.get('wifi_mac') or asset_data.get('ethernet_mac')
        if mac_val:
            mac = get_primary_mac_address(mac_val)
            if mac:
                mac_key = mac.replace(':', '').upper()  # ← Ensure uppercase
                match = self._index_by_mac.get(mac_key)
            if match:
                if self.debug:
                    print(f"    Match by MAC: {mac_val} -> ID {match['id']}")
                return match
        
        # 4. By exact name match (for static IP devices)
        name = asset_data.get('name')
        if name and not name.lower().startswith('device-'):
            match = self._index_by_name.get(name.lower())
            if match:
                if self.debug:
                    print(f"    Match by name: {name} -> ID {match['id']}")
                return match
        
        return None

    def record(self, asset_id: str, asset_data: Dict, action: str) -> None:
        """Cache the result."""
        cache_key = self._get_cache_key(asset_data)
        if cache_key and action == 'create':
            # For creates, we don't have the snipe_id yet
            # It will be set by the dispatcher after creation
            pass

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