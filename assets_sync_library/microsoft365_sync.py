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
from utils.mac_utils import combine_macs, normalize_mac

class Microsoft365Sync:
    """Microsoft365 data merging service"""
    
    def __init__(self):
        self.asset_matcher = AssetMatcher()
        self.microsoft365 = Microsoft365Service()
        self.intune_sync = IntuneScanner(self.asset_matcher)
        self.teams_sync = TeamsScanner(self.asset_matcher)
    
    def _prepare_asset_dictionaries(self, intune_data: List[Dict], teams_data: List[Dict]) -> tuple[Dict, Dict]:
        """Creates dictionaries of assets keyed by serial number for quick lookups."""
        print("Preparing asset dictionaries...")
        intune_assets_by_serial = {
            asset.get('serial').upper(): asset 
            for asset in intune_data if asset.get('serial')
        }
        teams_assets_by_serial = {
            asset.get('serial').upper(): asset 
            for asset in teams_data if asset.get('serial')
        }
        return intune_assets_by_serial, teams_assets_by_serial

    def _merge_intune_with_teams(self, intune_assets_by_serial: Dict, teams_assets_by_serial: Dict) -> tuple[List[Dict], set]:
        """Merges Teams data into Intune assets, prioritizing Intune data."""
        print("Merging transformed Intune assets with corresponding Teams data...")
        merged_assets = []
        processed_serials = set()

        for serial, intune_asset in intune_assets_by_serial.items():
            merged_asset = intune_asset.copy()
            teams_asset = teams_assets_by_serial.get(serial)
    
            if teams_asset:
                print(f"  ✓ Teams only: {serial}")
                final_asset = teams_asset.copy()
                final_asset.update(intune_asset)
                final_asset['last_update_source'] = 'microsoft365'
                final_asset['last_update_at'] = datetime.now(timezone.utc).isoformat()
                merged_assets.append(final_asset)
            else:
                merged_assets.append(merged_asset)
                print(f"  ✓ Intune only: {serial}")
            
            processed_serials.add(serial)
            
        return merged_assets, processed_serials

    def _add_unmatched_assets(self, merged_assets: List[Dict], processed_serials: set, intune_data: List[Dict], teams_assets_by_serial: Dict):
        """Adds assets from Teams and Intune that were not matched by serial number."""
        # Add Teams assets that were not found in Intune
        print("Adding unmatched Teams-only assets...")
        for serial, teams_asset in teams_assets_by_serial.items():
            if serial not in processed_serials:
                merged_assets.append(teams_asset)
        
        # Add Intune assets that did not have a serial number
        print("Adding unmatched Intune assets (without serial numbers)...")
        for intune_asset in intune_data:
            if not intune_asset.get('serial'):
                merged_assets.append(intune_asset)
        
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
        intune_assets_by_serial, teams_assets_by_serial = self._prepare_asset_dictionaries(intune_data, teams_data)
        
        # Perform the merge operations
        merged_assets, processed_serials = self._merge_intune_with_teams(intune_assets_by_serial, teams_assets_by_serial)
        self._add_unmatched_assets(merged_assets, processed_serials, intune_data, teams_assets_by_serial)

        return merged_assets
    
    def sync_to_snipeit(self):
        """Fetches, merges, and syncs all Microsoft 365 assets to Snipe-IT."""
        print("Starting Microsoft 365 synchronization...")
        
        self.asset_matcher.clear_all_caches()
        # Clear previous debug logs for this source at the start of the sync
        if debug_logger.microsoft365_debug:
            debug_logger.clear_logs('microsoft365')

        # Get the final, merged list of assets
        final_assets = self.merge_data()
        print(f"Total of {len(final_assets)} unique assets after merging Intune and Teams data.")
        
        # Log the final transformed payload before sending to the matcher
        if debug_logger.microsoft365_debug:
            debug_logger.log_parsed_asset_data('microsoft365', final_assets)
        
        # Process the final list with the asset matcher
        results = self.asset_matcher.process_scan_data('microsoft365', final_assets)
        
        if debug_logger.microsoft365_debug:
            debug_logger.log_sync_summary('microsoft365', results)
        
        print(f"Sync complete: {results['created']} created, {results['updated']} updated, {results['failed']} failed")
        return results

    def sync_to_logs(self):
        """Fetches live data and generates the raw and parsed log files for debugging."""
        print("Starting Microsoft 365 debug logging...")
        if not debug_logger.microsoft365_debug:
            print("Microsoft 365 debugging is not enabled. Set MICROSOFT365_DEBUG=1 to run this test.")
            return

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
    
