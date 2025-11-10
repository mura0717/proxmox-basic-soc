#!/usr/bin/env python3
"""
Debug script to quickly check if Teams assets are categorized correctly.
It uses the raw_teams_log.txt file and does not require live API calls.
"""

import os
import sys
import json
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets_sync_library.asset_categorizer import AssetCategorizer

class TeamsDebugCategorization:
    """Determines asset type and category for Teams devices from log files."""
    def __init__(self):
        self.debug = os.getenv('TEAMS_CATEGORIZATION_DEBUG', '0') == '1'
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(base_dir, "../logs/debug_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.teams_categorized_assets_from_log = os.path.join(self.log_dir, "teams_categorized_assets_from.log")
        self.raw_log_path = os.path.join(self.log_dir, "teams_raw_unparsed_data.log")

    def get_raw_teams_assets_from_log(self) -> List[Dict]:
        """Fetches all Teams assets from its specific raw log file."""
        if not os.path.exists(self.raw_log_path):
            print(f"Error: Log file not found at {self.raw_log_path}")
            print("Please run a Teams sync with TEAMS_DEBUG=1 first.")
            return []

        assets = []
        try:
            with open(self.raw_log_path, 'r', encoding='utf-8') as file:
                content = file.read()

            chunks = content.split('--- RAW DATA | Host:')

            for chunk in chunks[1:]:  # Skip the first item
                try:
                    json_start = chunk.find('{')
                    if json_start == -1: continue
                    json_text = chunk[json_start:]
                    assets.append(json.loads(json_text))
                except json.JSONDecodeError as e:
                    print(f"Warning: Failed to decode a JSON chunk. Error: {e}")
                    continue
        except Exception as e:
            print(f"Error reading or parsing log file: {e}")

        return assets

    def write_teams_assets_to_logfile(self):
        """Transforms and categorizes raw Teams assets, writing the result to a log."""
        from scanners.teams_sync import TeamsSync
        sync = TeamsSync()
        raw_assets = self.get_raw_teams_assets_from_log()
        print(f"Loaded {len(raw_assets)} raw assets from Teams log.")

        output_path = self.teams_categorized_assets_from_log
        with open(output_path, 'w', encoding='utf-8') as f:
            for asset in raw_assets:
                transformed = sync.transform_teams_to_snipeit(asset)
                categorization = AssetCategorizer.categorize(transformed)
                out = {
                    "display_name": transformed.get("primary_user_display_name"),
                    "asset_tag": transformed.get("asset_tag"),
                    'serial': transformed.get('serial'),
                    "manufacturer": transformed.get("manufacturer"),
                    "model": transformed.get("model"),
                    "device_type": categorization.get("device_type"),
                    "device_id": transformed.get("teams_device_id"),
                    "category": categorization.get("category"),
                    "mac": transformed.get("mac_addresses")
                }
                f.write(json.dumps(out, indent=2) + "\n")
        print(f"Wrote categorized results to {output_path}")

teams_debug_categorization = TeamsDebugCategorization()