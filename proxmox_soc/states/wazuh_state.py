"""
Wazuh State Manager
Tracks assets sent to Wazuh to prevent duplicates and detect changes.
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Optional

from proxmox_soc.states.base_state import BaseStateManager, StateResult
from proxmox_soc.utils.mac_utils import get_primary_mac_address


class WazuhStateManager(BaseStateManager):
    """
    File-based state tracking for Wazuh.
    """
    
    IDENTITY_FIELDS = ('serial', 'mac_addresses', 'intune_device_id', 'azure_ad_id')
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
        """Generate deterministic ID based on asset's immutable properties."""
        for field in self.IDENTITY_FIELDS:
            val = asset_data.get(field)
            if val:
                if field == 'mac_addresses':
                    mac = get_primary_mac_address(val)
                    if mac:
                        return f"{field}:{mac}"
                    continue
                return f"{field}:{str(val).strip()}"
        
        # Fallback: Use name if it's not generic
        name = asset_data.get('name')
        if name and name != "Unknown" and not name.lower().startswith('device-'):
            return f"name:{name}"
            
        return None

    def check(self, asset_data: Dict) -> StateResult:
        """Determine if asset is new, changed, or unchanged."""
        existing_id = self._find_existing_id(asset_data)
        asset_id = existing_id if existing_id else self.generate_id(asset_data)
        
        if not asset_id:
            return StateResult(
                action='skip',
                asset_id='',
                existing=None,
                reason='No suitable identifier'
            )
        
        current_hash = self._compute_hash(asset_data)
        
        # Case 1: New Asset
        if asset_id not in self._state:
            return StateResult(
                action='create',
                asset_id=asset_id,
                existing=None,
                reason='New asset'
            )

        # Case 2: Check for changes
        stored_hash = self._state[asset_id].get('data_hash')
        
        if current_hash == stored_hash:
            return StateResult(
                action='skip',
                asset_id=asset_id,
                existing=self._state[asset_id],
                reason='Data unchanged'
            )
        
        return StateResult(
            action='update',
            asset_id=asset_id,
            existing=self._state[asset_id],
            reason='Data changed'
        )
        
    def _find_existing_id(self, asset_data: Dict) -> Optional[str]:
        """
        Search state for any record matching this asset's identifiers.
        This prevents duplicates when the same device is seen from different sources
        with different primary identifiers.
        """
        # Extract all identifiers from incoming asset
        raw_serial = asset_data.get('serial')
        search_serial = raw_serial.strip().upper() if raw_serial else None
        
        search_mac = get_primary_mac_address(asset_data.get('mac_addresses'))
        search_intune_id = asset_data.get('intune_device_id')
        search_azure_id = asset_data.get('azure_ad_id')
        
        for stored_id, stored_data in self._state.items():
            # Check if stored ID matches any of our identifiers
            if search_serial and stored_id == f"serial:{search_serial}":
                return stored_id
            if search_mac and stored_id == f"mac_addresses:{search_mac}":
                return stored_id
            if search_intune_id and stored_id == f"intune_device_id:{search_intune_id}":
                return stored_id
            if search_azure_id and stored_id == f"azure_ad_id:{search_azure_id}":
                return stored_id
            
            # Also check stored metadata (if we store identifiers in the state)
            stored_serial = str(stored_data.get('serial') or '').strip().upper()
            stored_mac = stored_data.get('mac')
            
            if search_serial and stored_serial and search_serial == stored_serial:
                return stored_id
            if search_mac and stored_mac and search_mac == stored_mac:
                return stored_id
            
            stored_intune = stored_data.get('intune_device_id')
            if search_intune_id and stored_intune and str(search_intune_id) == str(stored_intune):
                return stored_id
        
        return None

    def record(self, asset_id: str, asset_data: Dict, action: str) -> None:
        """Record that an action was taken - now stores additional identifiers for cross-reference."""
        mac = get_primary_mac_address(asset_data.get('mac_addresses'))
        
        self._state[asset_id] = {
            'last_seen': datetime.now(timezone.utc).isoformat(),
            'data_hash': self._compute_hash(asset_data),
            'last_action': action,
            'name': asset_data.get('name'),
            # Store additional identifiers for cross-reference
            'serial': asset_data.get('serial', '').strip() if asset_data.get('serial') else None,
            'mac': mac,
            'intune_device_id': asset_data.get('intune_device_id'),
            'azure_ad_id': asset_data.get('azure_ad_id'),
        }
        self._dirty = True

    def _compute_hash(self, asset_data: Dict) -> str:
        """Hash only the fields that matter for updates."""
        relevant = {k: asset_data.get(k) for k in self.CHANGE_FIELDS if asset_data.get(k)}
        return hashlib.md5(json.dumps(relevant, sort_keys=True, default=str).encode()).hexdigest()
    