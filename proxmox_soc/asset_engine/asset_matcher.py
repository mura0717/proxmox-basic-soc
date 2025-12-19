"""
Centralized Asset Matching Service
Consolidates data from multiple sources to identify existing assets
"""

import os
from typing import Dict, List

from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService
from proxmox_soc.asset_engine.asset_finder import AssetFinder
from proxmox_soc.builders.snipe_builder import SnipePayloadBuilder
from proxmox_soc.config.network_config import STATIC_IP_MAP

class AssetMatcher:
    def __init__(self):
        self.asset_service = AssetService()
        self.finder = AssetFinder(self.asset_service)
        # Delegate formatting to the builder
        self.builder = SnipePayloadBuilder() 
        self.debug = os.getenv('ASSET_MATCHER_DEBUG', '0') == '1'

    def process_scan_data(self, scan_type: str, scan_data: List[Dict]) -> List[Dict]:
        """
        Main Pipeline Logic.
        Returns a list of actions. Does NOT call external APIs.
        """
        actions = []
        
        for asset_data in scan_data:
            # 1. Enrich
            asset_data['_source'] = scan_type
            self._enrich_with_static_map(asset_data)

            # 2. Match
            existing = self.find_existing_asset(asset_data)
            
            # 3. Decide Action
            if existing:
                # Merge logic
                flattened = {**existing}
                if isinstance(flattened.get('model'), dict): flattened['model'] = flattened['model'].get('name')
                if isinstance(flattened.get('manufacturer'), dict): flattened['manufacturer'] = flattened['manufacturer'].get('name')
                
                merged_data = self._merge_data({**flattened}, asset_data, scan_type)
                
                # Use Builder
                snipe_payload = self.builder.build(merged_data, is_update=True)
                actions.append(self._create_standard_object("update", existing['id'], snipe_payload, merged_data))
            
            elif self._has_sufficient_data(asset_data):
                # Use Builder
                snipe_payload = self.builder.build(asset_data, is_update=False)
                actions.append(self._create_standard_object("create", None, snipe_payload, asset_data))
            else:
                if self.debug: print(f"Skipped insufficient data: {asset_data.get('name')}")

        return actions

    def _create_standard_object(self, action, snipe_id, snipe_payload, raw_data):
        return {
            "action": action,
            "snipe_id": snipe_id,
            "snipe_payload": snipe_payload, # Formatted JSON for Snipe-IT
            "canonical_data": raw_data      # Raw data for Zabbix/Wazuh
        }

    def find_existing_asset(self, asset_data):
        return (
            self.finder.by_serial(asset_data.get('serial')) or
            self.finder.by_asset_tag(asset_data.get('asset_tag')) or
            self.finder.by_static_mapping(asset_data.get('last_seen_ip')) or
            self.finder.by_mac_address(asset_data) or
            self.finder.by_hostname(asset_data) or
            self.finder.by_ip_address(asset_data.get('last_seen_ip'))
        )

    def _merge_data(self, existing: Dict, new_data: Dict, scan_type: str) -> Dict:
        merged = {**existing, **new_data} # Simplified merge
        merged['_source'] = scan_type
        return merged

    def _has_sufficient_data(self, asset_data: Dict) -> bool:
        if asset_data.get('last_seen_ip') in STATIC_IP_MAP: return True
        if asset_data.get('serial') or asset_data.get('mac_addresses'): return True
        return False

    def _enrich_with_static_map(self, asset_data: Dict):
        ip = asset_data.get('last_seen_ip')
        if ip and ip in STATIC_IP_MAP: asset_data.update(STATIC_IP_MAP[ip])