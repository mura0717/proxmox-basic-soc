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

class Microsoft365DebugCategorization:
    """Determines asset type and category for merged M365 devices from log files."""
    def __init__(self):
        self.debug = os.getenv('MICROSOFT365_CATEGORIZATION_DEBUG', '0') == '1'
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(base_dir, "../logs/debug_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.m365_categorized_assets_from_log = os.path.join(self.log_dir, "microsoft365_categorized_assets_from.log")
        self.raw_log_path = os.path.join(self.log_dir, "microsoft365_raw_merged_data.log")

    def get_raw_m365_assets_from_log(self) -> List[Dict]:
        """Fetches all merged M365 assets from its specific raw log file."""
        if not os.path.exists(self.raw_log_path):
            print(f"Error: Log file not found at {self.raw_log_path}")
            print("Please run a Microsoft 365 sync with MICROSOFT365_DEBUG=1 first.")
            return []

        assets = []
        try:
            with open(self.raw_log_path, 'r', encoding='utf-8') as file:
                content = file.read()

            # The log contains one large JSON object under a 'merged-data' host
            json_start = content.find('{\n    "assets": [')
            if json_start != -1:
                data = json.loads(content[json_start:])
                assets = data.get('assets', [])
        except Exception as e:
            print(f"Error reading or parsing log file: {e}")

        return assets

    def write_m365_assets_to_logfile(self):
        """Categorizes raw merged M365 assets, writing the result to a log."""
        raw_assets = self.get_raw_m365_assets_from_log()
        print(f"Loaded {len(raw_assets)} raw merged assets from Microsoft 365 log.")

        output_path = self.m365_categorized_assets_from_log
        with open(output_path, 'w', encoding='utf-8') as f:
            for asset in raw_assets:
                # The asset is already transformed, so we just categorize it
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

microsoft365_debug_categorization = Microsoft365DebugCategorization()

if __name__ == "__main__":
    if microsoft365_debug_categorization.debug:
        from debug.tools.asset_debug_logger import debug_logger
        microsoft365_debug_categorization.write_m365_assets_to_logfile()
    else:
        print("To debug categorization, set MICROSOFT365_CATEGORIZATION_DEBUG=1 and run this script.")
        from debug.tools.asset_debug_logger import debug_logger
        debug_logger.clear_logs('microsoft365')
