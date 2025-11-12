"""
Utility for merging raw data coming from Microsoft365 API calls.
"""
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional
from msal import ConfidentialClientApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets_sync_library.asset_matcher import AssetMatcher
from debug.asset_debug_logger import debug_logger 
from config.microsoft365_service import Microsoft365Service
from scanners.intune_scanner import IntuneScanner
from scanners.teams_scanner import TeamsScanner
from utils.mac_utils import normalize_mac
from utils.text_utils import normalize_for_comparison
from config.mac_config import CTP18

class Microsoft365Sync:
    """Microsoft365 data merging service"""
    
    def __init__(self):
        self.asset_matcher = AssetMatcher()
        self.microsoft365 = Microsoft365Service()
        self.intune_sync = IntuneScanner(self.asset_matcher)
        self.teams_sync = TeamsScanner(self.asset_matcher)
    
    def _prepare_asset_dictionaries(self, intune_data: List[Dict], teams_data: List[Dict]) -> tuple[Dict, Dict, Dict, Dict]:
        """Creates dictionaries of assets keyed by various identifiers for quick lookups."""
        print("Preparing asset dictionaries...")
        intune_assets_by_serial = {
            asset.get('serial').upper(): asset 
            for asset in intune_data if asset.get('serial')
        }
        intune_assets_by_user_id = {
            asset.get('primary_user_id'): asset
            for asset in intune_data if asset.get('primary_user_id')
        }
        teams_assets_by_serial = {
            asset.get('serial').upper(): asset 
            for asset in teams_data if asset.get('serial')
        }
        teams_assets_by_user_id = {
            asset.get('primary_user_id'): asset
            for asset in teams_data if asset.get('primary_user_id')
        }
        return intune_assets_by_serial, teams_assets_by_serial, intune_assets_by_user_id, teams_assets_by_user_id

    def _merge_intune_with_teams(self, intune_assets_by_serial: Dict, teams_assets_by_serial: Dict, intune_assets_by_user_id: Dict, teams_assets_by_user_id: Dict) -> tuple[List[Dict], set]:
        """Merges Teams data into Intune assets, prioritizing Intune data."""
        print("Merging transformed Intune assets with corresponding Teams data...")
        merged_assets = []
        processed_ids = set()

        # Use a copy of the user ID dict to track which Teams assets have been merged
        unmerged_teams_by_user_id = teams_assets_by_user_id.copy()

        for intune_asset in intune_data:
            # Start with the Intune asset as the base
            final_asset = intune_asset.copy()
            serial = final_asset.get('serial')
            user_id = final_asset.get('primary_user_id')

            # Try to find a matching Teams asset by serial, then by primary user ID as a fallback
            teams_asset = None
            if serial:
                teams_asset = teams_assets_by_serial.get(serial.upper())
            if not teams_asset and user_id:
                teams_asset = teams_assets_by_user_id.get(user_id)
    
            if teams_asset:
                print(f"  ✓ Merging Teams data for: {serial or user_id}")
                # Merge: Teams data is added only if the key doesn't already exist in the Intune asset
                final_asset.update({k: v for k, v in teams_asset.items() if k not in final_asset})
                final_asset['last_update_source'] = 'microsoft365'
                final_asset['last_update_at'] = datetime.now(timezone.utc).isoformat()
                
                # Mark this teams asset as processed
                if user_id in unmerged_teams_by_user_id:
                    del unmerged_teams_by_user_id[user_id]
            
            merged_assets.append(final_asset)
            
        # Add any remaining Teams assets that didn't have a corresponding Intune object
        for teams_asset in unmerged_teams_by_user_id.values():
            print(f"  ✓ Adding Teams-only asset: {teams_asset.get('name')}")
            merged_assets.append(teams_asset)
            
        return merged_assets

    def _enrich_assets_with_static_macs(self, merged_assets: List[Dict]):
        """Adds MAC addresses from a static MAC address list for missing assets."""
        print("Enriching assets with static MAC addresses from mac_config...")
        
        static_mac_map = {
            device['serial']: device['mac_address']
            for device in CTP18.values() if 'serial' in device and 'mac_address' in device
        }
        
        for asset in merged_assets:
            if not asset.get('mac_addresses'):
                serial = asset.get('serial')
                if serial and serial in static_mac_map:
                    asset['mac_addresses'] = normalize_mac(static_mac_map[serial])
        
    def merge_data(self, intune_data: Optional[List[Dict]] = None, teams_data: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Merges Intune and Teams data. If data lists are not provided, fetches them from the scanners.
        """
        # Fetch data from scanners if not provided
        if intune_data is None or teams_data is None:
            raw_intune_data, intune_data = self.intune_sync.get_transformed_assets()
            raw_teams_data, teams_data = self.teams_sync.get_transformed_assets()
            
            # Log raw API data if debugging is enabled
            if debug_logger.microsoft365_debug:
                combined_raw_data = {'intune_assets': raw_intune_data, 'teams_assets': raw_teams_data}
                debug_logger.log_raw_host_data('microsoft365', 'raw-unmerged-data', combined_raw_data)
        
        # Prepare dictionaries keyed by serial number for efficient merging
        intune_assets_by_serial, teams_assets_by_serial, intune_assets_by_user_id, teams_assets_by_user_id = self._prepare_asset_dictionaries(intune_data, teams_data)
        
        # Perform the merge operations
        merged_assets = self._merge_intune_with_teams(intune_assets_by_serial, teams_assets_by_serial, intune_assets_by_user_id, teams_assets_by_user_id)
        
        # Enrich the final list with static MACs for devices that are missing them
        self._enrich_assets_with_static_macs(merged_assets)

        return merged_assets
    
    def sync_to_snipeit(self):
        """Fetches, merges, and syncs all Microsoft 365 assets to Snipe-IT."""
        print("Starting Microsoft 365 synchronization...")
        
        self.asset_matcher.clear_all_caches()
        # Clear previous debug logs for this source at the start of the sync
        if debug_logger.microsoft365_debug:
            debug_logger.clear_logs('microsoft365')

        # Get the final, merged list of assets
        merged_assets = self.merge_data()
        print(f"Total of {len(merged_assets)} unique assets after merging Intune and Teams data.")
        # Log the final transformed payload before sending to the matcher
        if debug_logger.microsoft365_debug:
            debug_logger.log_parsed_asset_data('microsoft365', merged_assets)
        
        # Process the final list with the asset matcher
        results = self.asset_matcher.process_scan_data('microsoft365', merged_assets)
        
        if debug_logger.microsoft365_debug:
            debug_logger.log_sync_summary('microsoft365', results)
        
        print(f"Sync complete: {results['created']} created, {results['updated']} updated, {results['failed']} failed")
        return results

    def sync_to_logs(self):
        """Fetches live data and generates the raw and parsed log files for debugging."""
        print("Starting Microsoft 365 debug logging...")

        # 1. Fetch live data once
        raw_intune_data, transformed_intune = self.intune_sync.get_transformed_assets()
        raw_teams_data, transformed_teams = self.teams_sync.get_transformed_assets()
        combined_raw_data = {'intune_assets': raw_intune_data, 'teams_assets': raw_teams_data}

        # 2. Clear old logs and write the new raw data log
        debug_logger.clear_logs('microsoft365')
        debug_logger.log_raw_host_data('microsoft365', 'raw-unmerged-data', combined_raw_data)
        print(f"\nRaw data log file has been created at: {debug_logger.log_files['microsoft365']['raw']}")

        # 3. Merge the already-fetched data and write the parsed data log
        merged_assets = self.merge_data(intune_data=transformed_intune, teams_data=transformed_teams)
        print(f"Found {len(merged_assets)} unique assets from Intune and Teams")
        debug_logger.log_parsed_asset_data('microsoft365', merged_assets)
        print(f"\nMerged transformed data log file has been created at: {debug_logger.log_files['microsoft365']['parsed']}")

if __name__ == "__main__":
    sync = Microsoft365Sync()
    if debug_logger.microsoft365_debug:
        sync.sync_to_logs()
    sync.sync_to_snipeit()
 

  
    
