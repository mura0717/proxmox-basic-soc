#!/usr/bin/env python3
"""
Teams Integration for Snipe-IT
Syncs assets from Microsoft Teams to Snipe-IT
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
from debug.teams_categorize_from_logs import teams_debug_categorization
from utils.mac_utils import combine_macs, normalize_mac

class TeamsSync:
    """Microsoft Teams synchronization service"""
    
    def __init__(self):
        self.asset_matcher = AssetMatcher()
        self.graph_url = "https://graph.microsoft.com/beta"
        self.microsoft365 = Microsoft365()
    
    def get_access_token(self) -> Optional[str]:
        """Ensure a valid access token is available and return it."""
        if not self.microsoft365.access_token:
            if not self.microsoft365.authenticate():
                print("Authentication failed via Microsoft365 helper.")
                return None
        return self.microsoft365.access_token
    
    def get_teams_assets(self) -> List[Dict]:
        """Fetch all teams devices from Microsoft Teams"""
        access_token = self.get_access_token()
        if not access_token:
            print("No access token available, cannot fetch Teams assets.")
            return []
 
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        assets = []
        url = f"{self.graph_url}/teamwork/devices"
        
        while url:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                if not data.get('value'):
                    print(f"DEBUG: API call to {url} returned an empty 'value' array.") # Keep this for immediate feedback
                    print(f"DEBUG: Full API Response: {json.dumps(data, indent=2)}")

                assets.extend(data.get('value', []))
                url = data.get('@odata.nextLink')  # Handle pagination
                
            except requests.exceptions.RequestException as e:
                if 'response' in locals() and response is not None:
                    print(f"Teams API Error - Response Status Code: {response.status_code}")
                    print(f"Teams API Error - Response Body: {response.text}")
                print(f"Error fetching assets: {e}")
                break
        
        return assets
    
    def testing_get_assets_to_log_and_terminal(self):
        teams_assets = self.get_teams_assets()
        print(f"Found {len(teams_assets)} assets in Teams")
        debug_logger.clear_logs('teams')
        
        logged_assets = []
        for asset in teams_assets:
            device_id = asset.get('id', 'unknown')
            debug_logger.log_raw_host_data('teams', device_id, asset)
            logged_assets.append(self.transform_teams_to_snipeit(asset))
            print(json.dumps(asset, indent=2))

        # Log the data after it has been transformed
        debug_logger.log_parsed_asset_data('teams', logged_assets)
        print(f"\nTeams debug log files have been created in the logs/debug_logs/ directory.")
 
            
    def transform_teams_to_snipeit(self, teams_asset: Dict) -> Dict:
        """Transform Teams asset data to Snipe-IT format"""
        current_time = datetime.now(timezone.utc).isoformat()
        hardware_details = teams_asset.get('hardwareDetail', {})
        current_user = teams_asset.get('currentUser', {})
        last_modified_by_user = (teams_asset.get('lastModifiedBy') or {}).get('user', {})
        
        # Map Teams fields to Snipe-IT custom fields
        transformed = {
            
            # Teams Specific
            'teams_device_id': teams_asset.get('id'),
            'teams_device_type': teams_asset.get('deviceType'),
            'teams_health_status': teams_asset.get('healthStatus'),
            'teams_activity_state': teams_asset.get('activityState'),
            'teams_last_modified': teams_asset.get('lastModifiedDateTime'),
            'teams_created_date': teams_asset.get('createdDateTime'),
            'teams_last_modified_by_id': last_modified_by_user.get('id'),
            'teams_last_modified_by_name': last_modified_by_user.get('displayName'),
            
            # Identity
            'asset_tag': teams_asset.get('companyAssetTag'),
            'serial': hardware_details.get('serialNumber'),
            'notes': teams_asset.get('notes'),
            
            # Hardware
            'manufacturer': hardware_details.get('manufacturer'),
            'model': hardware_details.get('model'),
            
            # Network
            'mac_addresses': combine_macs([
                normalize_mac(mac.split(':', 1)[-1])
                for mac in hardware_details.get('macAddresses', [])
                if mac
            ]),
            
            # Data Hygiene
            'last_update_source': 'teams',
            'last_update_at': current_time,
            
            # User 
            'primary_user_id': current_user.get('id'),
            'primary_user_display_name': current_user.get('displayName'),
            'identity_type': current_user.get('userIdentityType'),
            
        }

        # Remove None values
        return {k: v for k, v in transformed.items() if v is not None and v != ""}

    def get_transformed_assets(self) -> List[Dict]:
        """Fetches and transforms all assets from Teams."""
        print("Fetching and transforming Teams assets...")
        raw_assets = self.get_teams_assets()
        transformed_assets = [self.transform_teams_to_snipeit(asset) for asset in raw_assets]
        return transformed_assets

if __name__ == "__main__":
    # This script is now intended to be used as a library by Microsoft365Sync.
    # To test transformation, you can run the categorization debug script.
    print("This script is not meant to be run directly for syncing.")
    print("Use microsoft365_sync.py to perform a full sync.")
    # For direct testing of the raw data fetching and transformation:
    # sync = TeamsSync()
    # sync.testing_get_assets_to_log_and_terminal()

if __name__ == "__main__":
    if teams_debug_categorization.debug:
        debug_logger.clear_logs('teams')
        teams_debug_categorization.write_teams_assets_to_logfile()
    else:
        print("This script is not meant to be run directly for syncing.")
        print("Use microsoft365_sync.py to perform a full sync.")
        print("To debug categorization, set TEAMS_CATEGORIZATION_DEBUG=1 and run this script.")