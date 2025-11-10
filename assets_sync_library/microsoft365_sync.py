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
from config.microsoft365_config import Microsoft365
from scanners.intune_sync import IntuneSync
from scanners.teams_sync import TeamsSync
from utils.mac_utils import combine_macs, normalize_mac

class Microsoft365Sync:
    """Microsoft365 data merging service"""
    
    def __init__(self):
        self.asset_matcher = AssetMatcher()
        self.microsoft365 = Microsoft365()
        self.intune_sync = IntuneSync()
        self.teams_sync = TeamsSync()
    
    def fetch_teams_data(self) -> List[Dict]:
        """Fetches all device assets from Microsoft Teams."""
        print("Fetching Teams data...")
        return self.teams_sync.get_teams_assets()
    
    def fetch_intune_data(self) -> List[Dict]:
        """Fetches all managed device assets from Microsoft Intune."""
        print("Fetching Intune data...")
        return self.intune_sync.get_intune_assets()
    
    def _prepare_asset_dictionaries(self, intune_data: List[Dict], teams_data: List[Dict]) -> tuple[Dict, Dict]:
        """Creates dictionaries of assets keyed by serial number for quick lookups."""
        print("Preparing asset dictionaries...")
        intune_assets_by_serial = {
            asset.get('serialNumber'): asset 
            for asset in intune_data if asset.get('serialNumber')
        }
        teams_assets_by_serial = {
            (asset.get('hardwareDetail') or {}).get('serialNumber'): asset 
            for asset in teams_data if (asset.get('hardwareDetail') or {}).get('serialNumber')
        }
        return intune_assets_by_serial, teams_assets_by_serial

    def _merge_intune_with_teams(self, intune_assets_by_serial: Dict, teams_assets_by_serial: Dict) -> tuple[List[Dict], set]:
        """Merges Teams data into Intune assets, prioritizing Intune data."""
        print("Merging Intune assets with corresponding Teams data...")
        merged_assets = []
        processed_serials = set()

        for serial, intune_asset in intune_assets_by_serial.items():
            merged_asset = intune_asset.copy()
            teams_asset = teams_assets_by_serial.get(serial)

            if teams_asset:
                # Iterate through teams_asset and add data if the key is missing or the value is empty in the Intune asset.
                for key, value in teams_asset.items():
                    if not merged_asset.get(key):
                        merged_asset[key] = value
            
            merged_assets.append(merged_asset)
            processed_serials.add(serial)
        
        return merged_assets, processed_serials

    def _add_unmatched_assets(self, merged_assets: List[Dict], processed_serials: set, intune_data: List[Dict], teams_assets_by_serial: Dict):
        """Adds assets from Teams and Intune that were not matched by serial number."""
        # Add Teams assets that were not found in Intune
        print("Adding Teams-only assets...")
        for serial, teams_asset in teams_assets_by_serial.items():
            if serial not in processed_serials:
                merged_assets.append(teams_asset)
        
        # Add Intune assets that did not have a serial number
        print("Adding Intune assets without serial numbers...")
        for intune_asset in intune_data:
            if not intune_asset.get('serialNumber'):
                merged_assets.append(intune_asset)
        
    def merge_data(self) -> List[Dict]:
        """
        Merges data from Intune and Teams. Intune data is prioritized.
        Missing fields in an Intune asset are supplemented by the corresponding Teams asset.
        """
        # 1. Fetch data from both sources
        intune_data = self.fetch_intune_data()
        teams_data = self.fetch_teams_data()
        
        # 2. Prepare dictionaries for efficient merging
        intune_assets_by_serial, teams_assets_by_serial = self._prepare_asset_dictionaries(intune_data, teams_data)
        
        # 3. Perform the merge operations
        merged_assets, processed_serials = self._merge_intune_with_teams(intune_assets_by_serial, teams_assets_by_serial)
        self._add_unmatched_assets(merged_assets, processed_serials, intune_data, teams_assets_by_serial)

        return merged_assets
    
    def test_final_log(self):
        """
        Fetches, merges, and logs the combined raw asset data for debugging and verification.
        This does not transform or sync data to Snipe-IT.
        """
        final_assets = self.merge_data()
        print(f"Found {len(final_assets)} assets from Intune and Teams")
        
        # Clear the relevant log files before writing new data
        debug_logger.clear_logs('microsoft365')
        
        for asset in final_assets:
            # Use a reliable unique ID for logging, fallback through options
            device_id = asset.get('id') or asset.get('azureADDeviceId') or 'unknown'
            debug_logger.log_raw_host_data('microsoft365', device_id, asset)

        print(f"\nMerged raw data log file has been created at: {debug_logger.log_files['microsoft365']['raw']}")
    
    
if __name__ == "__main__":
    sync = Microsoft365Sync()
    sync.test_final_log()
    #sync.sync_to_snipeit()
        
        
        
        
    
