"""
Wazuh Asset State Manager
Tracks assets sent to Wazuh to prevent duplicates and detect changes.
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional

class WazuhStateManager:
    # 1. Identity Fields: Used to generate the Unique ID
    IDENTITY_FIELDS = ('serial', 'mac_addresses', 'intune_device_id', 'azure_ad_id')
    
    # 2. Change Detection Fields: Only updates to these trigger a new Wazuh log
    # We purposefully exclude 'last_seen' or 'timestamp' fields here.
    CHANGE_FIELDS = (
        'name', 'last_seen_ip', 'nmap_open_ports', 'nmap_os_guess',
        'intune_compliance', 'manufacturer', 'model', 'primary_user_email'
    )

    def __init__(self, state_file: Path):
        self.state_file = state_file
        self._state: Dict[str, Dict] = {}
        self._dirty = False
        self._load()

    def _load(self):
        """Load state from disk."""
        if self.state_file.exists():
            try:
                self._state = json.loads(self.state_file.read_text())
            except Exception:
                self._state = {}

    def save(self):
        """Persist state to disk only if data changed."""
        if self._dirty:
            self.state_file.parent.mkdir(parents=True, exist_ok=True)
            self.state_file.write_text(json.dumps(self._state, indent=2))
            self._dirty = False

    def generate_id(self, asset_data: Dict) -> Optional[str]:
        """Generates a deterministic ID based on the asset's immutable properties."""
        for field in self.IDENTITY_FIELDS:
            val = asset_data.get(field)
            if val:
                # Returns e.g., "serial:XY12345"
                return f"{field}:{str(val).strip()}"
        
        # Fallback: If we only have a name and it's not a generic device
        if asset_data.get('name') and asset_data.get('name') != "Unknown":
            return f"name:{asset_data['name']}"
            
        return None

    def _compute_hash(self, asset_data: Dict) -> str:
        """Hashes only the fields that matter for updates."""
        relevant = {k: asset_data.get(k) for k in self.CHANGE_FIELDS if asset_data.get(k)}
        return hashlib.md5(json.dumps(relevant, sort_keys=True, default=str).encode()).hexdigest()

    def process_asset(self, asset_data: Dict) -> tuple[str, Optional[str]]:
        """
        Determines the action: 'create', 'update', or 'skip'.
        Returns: (action, asset_id)
        """
        asset_id = self.generate_id(asset_data)
        if not asset_id:
            return 'skip', None # Cannot track anonymous assets

        current_hash = self._compute_hash(asset_data)
        
        # Case 1: New Asset
        if asset_id not in self._state:
            self._update_internal_state(asset_id, current_hash, asset_data)
            return 'create', asset_id

        # Case 2: Existing Asset - Check Hash
        stored_hash = self._state[asset_id].get('data_hash')
        if current_hash != stored_hash:
            self._update_internal_state(asset_id, current_hash, asset_data)
            return 'update', asset_id

        # Case 3: No Change
        return 'skip', asset_id

    def _update_internal_state(self, asset_id, data_hash, asset_data):
        self._state[asset_id] = {
            'last_seen': datetime.now(timezone.utc).isoformat(),
            'data_hash': data_hash,
            'name': asset_data.get('name') # Stored just for debugging readability
        }
        self._dirty = True