"""
Captures a snapshot of current Snipe-IT assets.
"""

import os
import sys
import json
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path

from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService

BASE_DIR = Path(__file__).resolve().parents[3]

class AssetSnapshotter:

    def __init__(self):
        self.asset_service = AssetService()
        self.snapshot_dir = BASE_DIR / "logs" / "snipe_snapshots"
        self.snapshot_dir.mkdir(parents=True, exist_ok=True)
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def take_snapshot(self, filename: Optional[str] = None) -> str:
        """
        Fetches all assets from Snipe-IT and saves them to a JSON file.
        """
        print("Taking snapshot of current Snipe-IT assets...")
        assets = self.asset_service.get_all(limit=10000, refresh_cache=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snipeit_snapshot_{timestamp}.json"
        
        filepath = self.snapshot_dir / filename
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(assets, f, indent=2, default=str)
        
        print(f"Snapshot saved to: {filepath}")
        return filepath

    def load_snapshot(self, filename: str) -> List[Dict]:
        """
        Loads assets from a previously saved snapshot file.
        """
        filepath = os.path.join(self.snapshot_dir, filename)
        if not os.path.exists(filepath):
            print(f"Error: Snapshot file not found at {filepath}")
            return []
        
        print(f"Loading snapshot from: {filepath}")
        with open(filepath, 'r', encoding='utf-8') as f:
            assets = json.load(f)
        
        print(f"Loaded {len(assets)} assets from snapshot.")
        return assets

if __name__ == "__main__":
    snapshotter = AssetSnapshotter()
    
    # If no arguments are given, default to taking a snapshot for cron jobs.
    if len(sys.argv) == 1:
        snapshotter.take_snapshot()
    else:
        command = sys.argv[1]
        if command == "take":
            custom_filename = sys.argv[2] if len(sys.argv) > 2 else None
            snapshotter.take_snapshot(filename=custom_filename)
        elif command == "load":
            if len(sys.argv) > 2:
                snapshotter.load_snapshot(sys.argv[2])
            else:
                print("Error: Please provide a filename to load.")
        else:
            print(f"Unknown command: {command}")
