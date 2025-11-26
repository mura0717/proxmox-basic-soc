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
        self.parsed_log_path = debug_logger.log_files['ms365']['parsed']
        self.categorization_log_path = debug_logger.log_files['ms365']['categorization']

    def get_parsed_ms365_assets_from_log(self) -> List[Dict]:
        """Fetches all transformed and merged M365 assets from the parsed log file."""
        if not os.path.exists(self.parsed_log_path):
            print(f"Error: Log file not found at {self.parsed_log_path}")
            print("Please run a Microsoft 365 sync with MS365_DEBUG=1 first to generate the log.")
            return []

        assets = []
        try:
            with open(self.parsed_log_path, 'r', encoding='utf-8') as file:
                content = file.read()
            
            # The parsed log file contains a JSON array of assets.
            # We need to find the start and end of the array to isolate it from headers/footers.
            start_index = content.find('[')
            end_index = content.rfind(']')
            
            if start_index != -1 and end_index != -1:
                json_text = content[start_index : end_index + 1]
                assets = json.loads(json_text)
        except Exception as e:
            print(f"Error reading or parsing log file: {e}")

        return assets

    def write_m365_assets_to_logfile(self):
        """Categorizes merged M365 assets from the parsed log file."""
        parsed_assets = self.get_parsed_ms365_assets_from_log()
        print(f"Loaded {len(parsed_assets)} parsed assets from Microsoft 365 log.")

        output_path = self.categorization_log_path
        with open(output_path, 'w', encoding='utf-8') as f:
            for asset in parsed_assets:
                categorization = AssetCategorizer.categorize(asset)
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
