"""
Utility for merging raw data coming from Microsoft365 API calls.
"""
import sys
import os
from datetime import datetime, timezone
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets_sync_library.asset_matcher import AssetMatcher
from debug.tools.asset_debug_logger import debug_logger 
from config.ms365_service import Microsoft365Service
from scanners.intune_scanner import IntuneScanner
from scanners.teams_scanner import TeamsScanner
from utils.mac_utils import normalize_mac
from debug.categorize_from_logs.ms365_categorize_from_logs import ms365_debug_categorization
from config.mac_config import CTP18

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
            asset.get('serial'): asset 
            for asset in intune_data if asset.get('serial')
        }
        teams_assets_by_serial = {
            asset.get('serial'): asset 
            for asset in teams_data if asset.get('serial')
        }
        
        print(f"  Intune assets with serial: {len(intune_assets_by_serial)}")
        print(f"  Teams assets with serial: {len(teams_assets_by_serial)}")
        
        # Create a lookup for Intune assets by user ID for fallback matching
        intune_assets_by_user_id = {}
        for asset in intune_data:
            if asset.get('primary_user_id'):
                intune_assets_by_user_id[asset['primary_user_id']] = asset
        
        return intune_assets_by_serial, teams_assets_by_serial

    def _merge_intune_with_teams(self, intune_assets_by_serial: Dict, teams_assets_by_serial: Dict) -> tuple[List[Dict], set]:
        """Merges Teams data into Intune assets, prioritizing Intune data."""
        print("Merging transformed Intune assets with corresponding Teams data...")
        merged_assets = []
        processed_serials = set()

        for serial, intune_asset in intune_assets_by_serial.items():
            intune_asset['_source'] = 'intune'  # Tag source for merge logic
            teams_asset = teams_assets_by_serial.get(serial)
    
            if teams_asset:
                if debug_logger.ms365_debug:
                    print(f"  ✓ Merging Teams data for: {serial}")
                teams_asset['_source'] = 'teams'
                # Use the robust, centralized merge function
                merged_asset = self.asset_matcher.merge_asset_data(teams_asset, intune_asset)
            else:
                if debug_logger.ms365_debug:
                    print(f"  ✓ Intune only: {serial}")
                merged_asset = intune_asset
            
            merged_assets.append(merged_asset)
            processed_serials.add(serial)
            
        return merged_assets, processed_serials

    def _handle_unmatched_teams_assets(self, merged_assets: List[Dict], processed_serials: set, teams_data: List[Dict], intune_data: List[Dict]):
        """Handles Teams assets not matched by serial, with a fallback merge on user ID."""
        if debug_logger.ms365_debug:
            print("Processing unmatched Teams-only assets...")
        intune_assets_by_user_id = {
            asset['primary_user_id']: asset 
            for asset in intune_data if asset.get('primary_user_id')
        }
        merged_assets_by_serial = {asset['serial']: asset for asset in merged_assets if asset.get('serial')}
        for teams_asset in teams_data:
            serial = teams_asset.get('serial')
            if serial and serial in processed_serials:
                continue # Already merged by serial
            user_id = teams_asset.get('primary_user_id')
            intune_match = intune_assets_by_user_id.get(user_id)
            intune_serial = intune_match.get('serial') if intune_match else None

            if intune_match and intune_serial in merged_assets_by_serial:
                # Fallback merge logic for shared user accounts
                if not serial:
                    if debug_logger.ms365_debug:
                        print(f"  ✓ Fallback merge for user ID {user_id} (Intune S/N: {intune_serial}, Teams asset has no S/N)")
                    merged_assets_by_serial[intune_serial].update(teams_asset)
                else:
                    if debug_logger.ms365_debug:
                        print(f"  ✗ Not merging for user ID {user_id}. Assets have different serials ({intune_serial} vs {serial}). Treating as separate devices.")
                    teams_asset['last_update_source'] = 'microsoft365'
                    teams_asset['last_update_at'] = datetime.now(timezone.utc).isoformat()
                    merged_assets.append(teams_asset)
            else:
                # This is a truly unmatched Teams asset
                if debug_logger.ms365_debug:
                    print(f"  ✓ Teams only: {serial or teams_asset.get('name', 'Unknown')}")
                # Ensure source metadata is set for truly unmatched Teams assets
                teams_asset['last_update_source'] = 'microsoft365'
                teams_asset['last_update_at'] = datetime.now(timezone.utc).isoformat()
                merged_assets.append(teams_asset)
    
    def _handle_unmatched_intune_assets(self, merged_assets: List[Dict], intune_data: List[Dict]):
        """Adds Intune assets that did not have a serial number."""
        if debug_logger.ms365_debug:
            print("Processing unmatched Intune assets (without serial numbers)...")
        for intune_asset in intune_data:
            if not intune_asset.get('serial'):
                merged_assets.append(intune_asset)

    def _add_unmatched_assets(self, merged_assets: List[Dict], processed_serials: set, intune_data: List[Dict], teams_data: List[Dict]):
        """Orchestrates the addition of assets that were not matched by serial number."""
        self._handle_unmatched_teams_assets(merged_assets, processed_serials, teams_data, intune_data)
        self._handle_unmatched_intune_assets(merged_assets, intune_data)
    
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
            if debug_logger.ms365_debug:
                combined_raw_data = {'intune_assets': raw_intune_data, 'teams_assets': raw_teams_data}
                debug_logger.log_raw_host_data('ms365', 'raw-unmerged-data', combined_raw_data)
        
        # Prepare dictionaries keyed by serial number for efficient merging
        intune_assets_by_serial, teams_assets_by_serial = self._prepare_asset_dictionaries(intune_data, teams_data) # This can be simplified now
        
        # Perform the merge operations
        merged_assets, processed_serials = self._merge_intune_with_teams(intune_assets_by_serial, teams_assets_by_serial)
        self._add_unmatched_assets(merged_assets, processed_serials, intune_data, teams_data)
        
        # Enrich the final list with static MACs for devices that are missing them
        self._enrich_assets_with_static_macs(merged_assets)

        return merged_assets
    
    def sync_to_snipeit(self):
        """Fetches, merges, and syncs all Microsoft 365 assets to Snipe-IT."""
        print("Starting Microsoft 365 synchronization...")
        
        self.asset_matcher.clear_all_caches()
        # Clear previous debug logs for this source at the start of the sync
        if debug_logger.ms365_debug:
            debug_logger.clear_logs('ms365')

        # Get the final, merged list of assets
        merged_assets = self.merge_data()
        print(f"Total of {len(merged_assets)} unique assets after merging Intune and Teams data.")
        # Log the final transformed payload before sending to the matcher
        if debug_logger.ms365_debug:
            debug_logger.log_parsed_asset_data('ms365', merged_assets)
        
        # Process the final list with the asset matcher
        results = self.asset_matcher.process_scan_data('ms365', merged_assets)
        
        if debug_logger.ms365_debug:
            debug_logger.log_sync_summary('ms365', results)
        
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
        debug_logger.clear_logs('ms365')
        debug_logger.log_raw_host_data('ms365', 'raw-unmerged-data', combined_raw_data)
        print(f"\nRaw data log file has been created at: {debug_logger.log_files['ms365']['raw']}")

        # 3. Merge the already-fetched data and write the parsed data log
        merged_assets = self.merge_data(intune_data=transformed_intune, teams_data=transformed_teams)
        print(f"Found {len(merged_assets)} unique assets from Intune and Teams")
        debug_logger.log_parsed_asset_data('ms365', merged_assets)
        print(f"\nMerged transformed data log file has been created at: {debug_logger.log_files['ms365']['parsed']}")

def main():
    """Main execution function for Microsoft 365 sync."""
    # If categorization debug is on, just run that and exit.
    if ms365_debug_categorization.debug:
        print("Running Microsoft 365 categorization from existing logs...")
        ms365_debug_categorization.write_m365_assets_to_logfile()
        return

    sync = Microsoft365Sync()
    if debug_logger.ms365_debug:
        sync.sync_to_logs() 
        return 
    sync.sync_to_snipeit()
 
if __name__ == "__main__":
    main()

  
    
