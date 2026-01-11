"""
The logic in this module has been refactored and moved to AssetResolver and AssetFinder.
It is retained here for reference and comparison during the transition.
"""

import os
from typing import Dict, List

from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService
from proxmox_soc.asset_engine.asset_finder import AssetFinder
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


    def _create_action_object(self, action, snipe_id, raw_data):
        return {
            "action": action,
            "snipe_id": snipe_id,
            "canonical_data": raw_data
        }

    