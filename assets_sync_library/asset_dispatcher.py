"""
Dispatches asset data to various services like Snipe-IT, Zabbix, and Wazuh.
"""
import os
import sys
from typing import Dict, Optional, List

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.services.assets import AssetService
from debug.tools.asset_debug_logger import debug_logger

class SnipeITDispatcher:
    """Handles sending data specifically to the Snipe-IT API."""
    def __init__(self):
        self.asset_service = AssetService()
        self.debug = os.getenv('DISPATCHER_DEBUG', '0') == '1'

    def dispatch(self, action: str, asset_id: Optional[int], snipe_payload: Dict, canonical_asset: Dict) -> Optional[Dict]:
        """
        Dispatches a create or update action to Snipe-IT.

        Args:
            action: The action to perform ('create' or 'update').
            asset_id: The ID of the asset to update (if applicable).
            snipe_payload: The prepared data payload for the Snipe-IT API.
            canonical_asset: The full, merged asset data for logging or other dispatchers.

        Returns:
            The result from the Snipe-IT API call.
        """
        asset_name = canonical_asset.get('name', 'Unknown')
        source = canonical_asset.get('_source', 'unknown')

        if debug_logger.is_enabled:
            debug_logger.log_final_payload(source, action, asset_name, snipe_payload)

        if action == 'create':
            print(f"  [DISPATCH] Creating new asset in Snipe-IT: {asset_name}")
            return self.asset_service.create(snipe_payload)
        elif action == 'update' and asset_id:
            print(f"  [DISPATCH] Updating asset in Snipe-IT: {asset_name} (ID: {asset_id})")
            return self.asset_service.update(asset_id, snipe_payload)
        
        print(f"  [DISPATCH] Invalid action '{action}' or missing asset_id for update. Skipping Snipe-IT dispatch.")
        return None

class MasterDispatcher:
    """A central dispatcher to route asset data to all relevant services."""
    def __init__(self):
        # In the future, you can add Zabbix and Wazuh dispatchers here.
        self.dispatchers = [
            SnipeITDispatcher(),
        ]

    def dispatch(self, action: str, asset_id: Optional[int], snipe_payload: Dict, canonical_asset: Dict):
        for dispatcher in self.dispatchers:
            dispatcher.dispatch(action, asset_id, snipe_payload, canonical_asset)
