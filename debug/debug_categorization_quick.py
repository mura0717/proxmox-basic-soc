#!/usr/bin/env python3
"""
Debug script to quickly check if assets are categorized correctly 
It doesn't need to Intune or Snipe-It via API since it uses raw_intune_log.txt file.
"""

import os
import sys
import json
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.asset_categorizer import DeviceCategorizer

class DebugCategorization:
    """Determines device type and category based on attributes.""" 
    def __init__(self):
        self.debug = os.getenv('CATEGORIZATION_DEBUG', '0') == '1'
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(base_dir, "../logs/debug_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.categorized_assets_log = os.path.join(self.log_dir, "categorized_assets_log.txt")
        self.raw_log_path = os.path.join(self.log_dir, "raw_intune_log.txt")

    
    def get_managed_devices(self) -> List[Dict]:
        """Fetch all managed devices from raw_intune_log.txt"""
        raw_log_path = self.raw_log_path
        devices = []
        try:
            with open(raw_log_path, 'r') as file:
                raw_data = file.read()
                for chunk in raw_data.split('--- RAW INTUNE DEVICE ---'):
                    chunk = chunk.strip()
                    if not chunk:
                        continue
                    start = chunk.find('{')
                    end = chunk.rfind('}')
                    if start == -1 or end == -1 or end <= start:
                        continue
                    json_text = chunk[start:end+1].strip()
                    try:
                        devices.append(json.loads(json_text))
                    except Exception as e:
                        print(f"JSON decode error: {e} | chunk: {json_text[:80]!r}")
        except Exception as e:
            print(f"Error reading raw_intune_log.txt: {e}")
        return devices
    
    def write_managed_devices_to_logfile(self):
        from scanners.intune_sync import IntuneSync
        sync = IntuneSync()
        raw_devices = self.get_managed_devices()
        print(f"Loaded {len(raw_devices)} raw devices from log.")

        # Transform and categorize each device
        output_path = self.categorized_assets_log
        with open(output_path, 'w', encoding='utf-8') as f:
            for device in raw_devices:
                transformed = sync.transform_intune_to_snipeit(device)
                categorization = DeviceCategorizer.categorize(transformed)
                out = {
                    "name": transformed.get("name"),
                    'serial': transformed.get('serial'),
                    "manufacturer": transformed.get("manufacturer"),
                    "model": transformed.get("model"),
                    "os_platform": transformed.get("os_platform"),
                    "device_type": categorization.get("device_type"),
                    "category": categorization.get("category"),
                    "cloud_provider": categorization.get("cloud_provider"),
                }
                f.write(json.dumps(out, indent=2) + "\n")
        print(f"Wrote categorized results to {output_path}")

debug_categorization = DebugCategorization()