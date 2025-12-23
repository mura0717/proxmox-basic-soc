"""
Core Asset Matching Service
Finds & Consolidates data from multiple sources
Produces action objects
"""

import os
from typing import Dict, List, Optional

from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService
from proxmox_soc.asset_engine.asset_finder import AssetFinder
from proxmox_soc.config.network_config import STATIC_IP_MAP
from proxmox_soc.config.snipe_schema import CUSTOM_FIELDS
from proxmox_soc.debug.tools.asset_debug_logger import debug_logger

class AssetMatcher:
    def __init__(self):
        self.asset_service = AssetService()
        self.finder = AssetFinder(self.asset_service)
        self.debug = os.getenv('ASSET_MATCHER_DEBUG', '0') == '1'

    def process_scan_data(self, scan_type: str, scan_data: List[Dict]) -> List[Dict]:
        """
        Returns list of dicts with:
        - action: 'create' or 'update'
        - snipe_id: ID of existing asset (for updates) or None
        - canonical_data: merged/enriched data for all systems
        """
        actions = []
        results = {'created': 0, 'updated': 0, 'skipped': 0}
        
        for asset_data in scan_data:
            # 1. Enrich
            asset_data['_source'] = scan_type
            self._enrich_with_static_map(asset_data)

            # 2. Match
            existing = self.find_existing_asset(asset_data)
            
            # 3. Decide Action
            if existing:
                merged = self._merge_with_existing(existing, asset_data, scan_type)
                
                # Use helper method
                action_obj = self._create_action_object("update", existing['id'], merged)
                actions.append(action_obj)
                
                results['updated'] += 1
                if self.debug:
                    print(f"  ✓ Update: {merged.get('name')} (ID: {existing['id']})")
            
            elif self._has_sufficient_data(asset_data):
                action_obj = self._create_action_object("create", None, asset_data)
                actions.append(action_obj)
                
                results['created'] += 1
                if self.debug:
                    print(f"  + Create: {asset_data.get('name')}")
            
            else:
                results['skipped'] += 1
                if self.debug:
                    print(f"  ✗ Skip: {asset_data.get('name', 'Unknown')} (insufficient data)")

        print(f"Matched {len(scan_data)} assets: "
              f"{results['created']} create, {results['updated']} update, {results['skipped']} skip")
        
        if self.debug:
            debug_logger.log_sync_summary(scan_type, results)
        
        return actions

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
    
    def _create_action_object(self, action, snipe_id, raw_data):
        return {
            "action": action,
            "snipe_id": snipe_id,
            "canonical_data": raw_data
        }

    def _merge_with_existing(self, existing: Dict, new_data: Dict, scan_type: str) -> Dict:
        """Merge new scan data with existing asset data."""
        merged = self._flatten_existing_asset(existing)
        
        # Fields where new scan data always wins
        priority_fields = {
            'nmap': ['last_seen_ip', 'nmap_last_scan', 'nmap_open_ports', 
                     'nmap_services', 'nmap_os_guess', 'open_ports_hash'],
            'microsoft365': ['intune_last_sync', 'intune_compliance', 
                            'primary_user_upn', 'primary_user_email'],
        }.get(scan_type, [])
        
        for key, value in new_data.items():
            if value in (None, '', []):
                continue
            # New data wins for: priority fields, or if existing is empty
            if key in priority_fields or not merged.get(key):
                merged[key] = value
        
        merged['_source'] = scan_type
        return merged

    def _flatten_existing_asset(self, existing: Dict) -> Dict:
        """Flatten Snipe-IT API response to simple key-value pairs."""
        flattened = {}
        
        for key, value in existing.items():
            if key == 'custom_fields':
                continue
            elif isinstance(value, dict):
                flattened[key] = value.get('name') or value.get('id')
            else:
                flattened[key] = value
        
        # Flatten custom fields by matching labels to keys
        for label, field_data in existing.get('custom_fields', {}).items():
            value = field_data.get('value') if isinstance(field_data, dict) else field_data
            for key, field_def in CUSTOM_FIELDS.items():
                if field_def.get('name') == label:
                    flattened[key] = value
                    break
        
        return flattened
    
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

    def _enrich_with_static_map(self, asset_data: Dict):
        """Enrich asset with data from static IP map (fills gaps only)."""
        ip = asset_data.get('last_seen_ip')
        if ip and ip in STATIC_IP_MAP:
            for key, value in STATIC_IP_MAP[ip].items():
                if not asset_data.get(key):
                    asset_data[key] = value
    
    def reset_finder_cache(self):
        """Reset finder cache between scan types in same process."""
        self.finder._all_assets_cache = None