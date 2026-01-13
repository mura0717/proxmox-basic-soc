"""CRUD service for Snipe-IT assets"""

from typing import Dict, Optional

from proxmox_soc.snipe_it.snipe_api.services.crudbase import CrudBaseService
from proxmox_soc.snipe_it.snipe_api.snipe_client import make_api_request

class AssetService(CrudBaseService):
    """Service for managing categories"""
    
    def __init__(self):
        super().__init__('/api/v1/hardware', 'hardware')
        
    def search_by_serial(self, serial: str) -> Optional[Dict]:
        resp = make_api_request("GET", f"{self.endpoint}/byserial/{serial}")
        if not resp:
            return None
        js = resp.json()
        if isinstance(js, dict):
            if js.get("rows"):
                return js["rows"][0]
            if js.get("id"):
                return js
        return None
    
    def search_by_asset_tag(self, asset_tag: str) -> Optional[Dict]:
        """Search for asset by asset tag"""
        response = make_api_request("GET", f"{self.endpoint}/bytag/{asset_tag}")
        if response and response.json().get("id"):
            return response.json()
        return None
    
    def get_all(self, limit: 10000, refresh_cache: bool = True) ->  Dict:
        """Get all assets, with optional cache refresh"""
        response = make_api_request("GET", f"{self.endpoint}?limit={limit}&refresh_cache={'true' if refresh_cache else 'false'}")
        if response:
            return response.json().get("rows", []) if response else []
        return []