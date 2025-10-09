"""CRUD service for Snipe-IT assets"""
import os
import sys
from typing import Dict, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crud.base import BaseCRUDService

class AssetService(BaseCRUDService):
    """Service for managing categories"""
    
    def __init__(self):
        super().__init__('/api/v1/hardware', 'hardware')
        
    def search_by_serial(self, serial: str) -> Optional[Dict]:
        from snipe_api.api_client import make_api_request
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
        from snipe_api.api_client import make_api_request
        response = make_api_request("GET", f"{self.endpoint}/bytag/{asset_tag}")
        if response and response.json().get("id"):
            return response.json()
        return None