"""
Utility for merging raw data coming from Microsoft365 API calls.
"""
import os
import sys
import requests
import json
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
    
    def fetch_teams_data():
        teams_assets = TeamsSync.get_teams_assets()
        teams_raw_data = []
        for asset in teams_assets:
            teams_raw_data.append(asset)
        return teams_raw_data
    
    def fetch_intune_data():
        intune_assets = IntuneSync.get_intune_assets()
        intune_raw_data = []
        for assets in intune_assets:
            intune_raw_data.append(IntuneSync.get_intune_assets())
        return intune_raw_data
        
    def compare_data(self):
        intune_data = self.fetch_intune_data()
        teams_data = self.fetch_teams_data()
        full_data = []
        
        for data in teams_data:
            if data in intune_data:
                continue
            else: 
                intune_data.append(intune_data)
        
        full_data = intune_data
        return full_data
    
    def prioratize_data(self):
        #Prioritize intune data first. And then add the missing parts coming from teams.
        pass
    
    def merge_data(self):
        final_raw_data = []
        self.compare_data()
        self.prioratize_data()
        return final_raw_data
    
    def transfrom_for_snipeit(self, intune_asset: Dict, teams_asset: Dict) -> Dict:
        pass
    
    def sync_to_snipeit():
        pass
    
    def test_final_log(self):
        final_assets = self.merge_data()
        print(f"Found {len(final_assets)} assets from Intune and Teams")
        debug_logger.clear_logs('teams', 'intune')
        
        logged_assets = []
        for asset in final_assets:
            device_id = asset.get('id', 'unknown')
            debug_logger.log_raw_host_data('microsoft365', device_id, asset)
            logged_assets.append(self.transfrom_for_snipeit(asset))
            print(json.dumps(asset, indent=2))

        # Log the data after it has been transformed
        debug_logger.log_parsed_asset_data('teams', logged_assets)
        print(f"\nFinal payload log file have been created in the logs/debug_logs/ directory.")
    
    
if __name__ == "__main__":
    sync = Microsoft365Sync()
    sync.test_final_log()
    #sync.sync_to_snipeit()
        
        
        
        
    
