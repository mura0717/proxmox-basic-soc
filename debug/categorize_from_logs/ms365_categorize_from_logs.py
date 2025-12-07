#!/usr/bin/env python3
"""
Debug script to quickly check if merged Microsoft 365 assets are categorized correctly.
It uses the microsoft365_raw_merged_data.log file and does not require live API calls.
"""

import os
import sys
import json
from typing import List, Dict

# Add the project root directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from assets_sync_library.asset_categorizer import AssetCategorizer
from debug.tools.asset_debug_logger import debug_logger

class Microsoft365DebugCategorization:
    """Determines asset type and category for merged M365 devices from log files."""
    def __init__(self):
        self.debug = os.getenv('MS365_CATEGORIZATION_DEBUG', '0') == '1'
        self.raw_log_path = debug_logger.log_files['ms365']['raw']
        self.categorization_log_path = debug_logger.log_files['ms365']['categorization']

    def get_raw_ms365_assets_from_log(self) -> List[Dict]:
        """Fetches all transformed and merged M365 assets from the raw log file."""
        if not os.path.exists(self.raw_log_path):
            print(f"Error: Log file not found at {self.raw_log_path}")
            print("Please run a Microsoft 365 sync with MS365_DEBUG=1 first to generate the log.")
            return []

        assets = []
        try:
            with open(self.raw_log_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # The raw log for ms365 contains a single JSON object with 'intune_assets' and 'teams_assets'
            # We need to find the main JSON structure and extract those lists.
            json_start = content.find('{')
            if json_start == -1:
                print(f"Warning: Could not find the start of a JSON object in {self.raw_log_path}")
                return []
            
            json_data = json.loads(content[json_start:])
            # Find the matching closing brace for the main object to isolate the JSON
            json_end = content.rfind('}')
            if json_end == -1:
                return []
            
            json_data = json.loads(content[json_start : json_end + 1])
            
            # The raw log contains the un-transformed data, so we need to transform it.
            intune_assets = json_data.get('intune_assets', [])
            teams_assets = json_data.get('teams_assets', [])
            
            assets.extend(intune_assets)
            assets.extend(teams_assets)

        except json.JSONDecodeError as e:
            print(f"Error decoding JSON from log file: {e}")
        except Exception as e:
            print(f"An unexpected error occurred: {e}")

        return assets

    def write_m365_assets_to_logfile(self):
        """Categorizes merged M365 assets from the raw log file."""
        # Import scanners directly to use their transformation logic without full initialization
        from scanners.intune_scanner import IntuneScanner
        from scanners.teams_scanner import TeamsScanner
        from assets_sync_library.ms365_sync import Microsoft365Sync # For merge logic only

        # Create lightweight instances, no AssetMatcher is needed here.
        intune_transformer = IntuneScanner()
        teams_transformer = TeamsScanner()
        merger = Microsoft365Sync()

        raw_assets = self.get_raw_ms365_assets_from_log()
        print(f"Loaded {len(raw_assets)} raw assets from Microsoft 365 log.")

        output_path = self.categorization_log_path
        with open(output_path, 'w', encoding='utf-8') as f:
            # Transform the raw data, then merge it.
            transformed_assets = [intune_transformer.transform_intune_to_snipeit(asset) for asset in raw_assets]
            merged_assets = merger.merge_data(intune_data=transformed_assets, teams_data=[]) # Simplified for categorization
            for asset in merged_assets:
                categorization = AssetCategorizer.categorize(asset) # Categorize the *merged* asset
                out = {
                    "name": asset.get("name"),
                    'serial': asset.get('serial'),
                    "manufacturer": asset.get("manufacturer"),
                    "model": asset.get("model"),
                    "os_platform": asset.get("os_platform"),
                    "last_update_source": asset.get("last_update_source"),
                    "device_type": categorization.get("device_type"),
                    "category": categorization.get("category"),
                }
                f.write(json.dumps(out, indent=2) + "\n")
        print(f"Wrote categorized results to {output_path}")

ms365_debug_categorization = Microsoft365DebugCategorization()

if __name__ == "__main__":
    if ms365_debug_categorization.debug:
        from debug.tools.asset_debug_logger import debug_logger
        ms365_debug_categorization.write_m365_assets_to_logfile()
    else:
        print("To debug categorization, set MS365_CATEGORIZATION_DEBUG=1 and run this script.")
