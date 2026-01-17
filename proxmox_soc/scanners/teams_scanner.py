#!/usr/bin/env python3
"""
Teams Integration
Syncs assets from Microsoft Teams to MS365 Aggregator
"""

import requests
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional

from proxmox_soc.debug.tools.asset_debug_logger import debug_logger
from proxmox_soc.config.ms365_service import Microsoft365Service
from proxmox_soc.debug.categorize_from_logs.teams_categorize_from_logs import teams_debug_categorization
from proxmox_soc.utils.mac_utils import combine_macs, macs_from_string

class TeamsScanner:
    """Microsoft Teams synchronization service"""
    
    def __init__(self):
        self.graph_url = "https://graph.microsoft.com/beta"
        self.ms365_service = Microsoft365Service()
    
    def get_access_token(self) -> Optional[str]:
        """Ensure a valid access token is available and return it."""
        if not self.ms365_service.access_token:
            if not self.ms365_service.authenticate():
                print("Authentication failed via Microsoft365 helper.")
                return None
        return self.ms365_service.access_token
    
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
 
            
    def normalize_asset(self, teams_asset: Dict) -> Dict:
        """Transform Teams asset data to Snipe-IT format"""
        current_time = datetime.now(timezone.utc).isoformat()
        hardware_details = teams_asset.get('hardwareDetail', {})
        current_user = teams_asset.get('currentUser', {})
        last_modified_by_user = (teams_asset.get('lastModifiedBy') or {}).get('user', {})
        serial_raw = hardware_details.get("serialNumber") or ""
        serial = serial_raw.upper() if serial_raw else None
        all_macs = []
        for raw_mac in (hardware_details.get('macAddresses') or []):
            # macs_from_string handles prefixed strings, plain MACs, any separator
            extracted = macs_from_string(str(raw_mac))
            all_macs.extend(extracted)
        
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
            'name': teams_asset.get('displayName') or teams_asset.get('hostname') or current_user.get('displayName'),
            'serial': serial,
            'notes': teams_asset.get('notes'),
            
            # Hardware
            'manufacturer': hardware_details.get('manufacturer'),
            'model': hardware_details.get('model'),
            
            # Network
            'mac_addresses': combine_macs(all_macs),
            
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

    def write_to_logs(self, raw_assets: List[Dict], transformed_assets: List[Dict]):
        """Write raw assets to debug logs. Assumes logs have been cleared."""
        for raw_asset, transformed_asset in zip(raw_assets, transformed_assets):
            asset_id = raw_asset.get('id', 'Unknown')
            debug_logger.log_raw_host_data('teams', asset_id, raw_asset)
            debug_logger.log_parsed_asset_data('teams', transformed_asset)

    def get_transformed_assets(self) -> tuple[List[Dict], List[Dict]]:
        """Fetches and transforms all assets from Teams, handling debug logic."""
        # If categorization debug is on, just run that and exit.
        if teams_debug_categorization.debug:
            print("Running Teams categorization from existing logs...")
            teams_debug_categorization.write_teams_assets_to_logfile()
            return [], [] # Return empty lists as no new scan was performed

        print("Fetching and transforming Teams assets...")
        raw_assets = self.get_teams_assets()
        transformed_assets = [self.normalize_asset(asset) for asset in raw_assets]

        if debug_logger.teams_debug:
            debug_logger.clear_logs('teams') # Clear logs before writing new data
            self.write_to_logs(raw_assets, transformed_assets)

        return raw_assets, transformed_assets

def main():
    # If categorization debug is on, just run that and exit.
    if teams_debug_categorization.debug:
        print("Running Teams categorization from existing logs...")
        teams_debug_categorization.write_teams_assets_to_logfile()
        return
    print("This script is not intended to be run directly. Use ms365_sync.py instead.")

if __name__ == "__main__":
    main()
