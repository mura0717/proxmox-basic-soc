import os
import sys
import json
from typing import List, Dict

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class SnipeItSnapshotter:
    """
    Captures a snapshot of current Snipe-IT assets.
    """
    def __init__(self):
        from crud.assets import AssetService
        self.asset_service = AssetService()
        self.snapshot_dir = "snapshots"
        os.makedirs(self.snapshot_dir, exist_ok=True)

    def take_snapshot(self, filename: str = None) -> str:
        """
        Fetches all assets from Snipe-IT and saves them to a JSON file.
        """
        print("Taking snapshot of current Snipe-IT assets...")
        assets = self.asset_service.get_all(limit=10000, refresh_cache=True)
        
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"snipeit_snapshot_{timestamp}.json"
        
        filepath = os.path.join(self.snapshot_dir, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
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
    from datetime import datetime
    snapshotter = SnipeItSnapshotter()
    
    if len(sys.argv) > 1:
        command = sys.argv[1]
        
        if command == "take":
            snapshotter.take