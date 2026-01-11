import os
from typing import Dict, List, Optional

from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService
from proxmox_soc.asset_engine.asset_finder import AssetFinder
from proxmox_soc.config.network_config import STATIC_IP_MAP
from proxmox_soc.config.snipe_schema import CUSTOM_FIELDS
from proxmox_soc.debug.tools.asset_debug_logger import debug_logger

class AssetResolver:
    
    def __init__(self):
        self.asset_service = AssetService()
        self.finder = AssetFinder(self.asset_service)
        self.debug = os.getenv('ASSET_RESOLVER_DEBUG', '0') == '1' 
        
    def resolve(self, scan_source: str, scan_data: List[Dict]) -> List[Dict]:
        resolved_assets = []
        for asset_data in scan_data:
            # 1. Tag Source
            asset_data['_source'] = scan_source
            self._enrich_with_static_map(asset_data)
            
            # 2. Enrich (Static IP Map)
            ip = asset_data.get('last_seen_ip')
            if ip and ip in STATIC_IP_MAP:
                for key, value in STATIC_IP_MAP[ip].items():
                    if not asset_data.get(key):
                        asset_data[key] = value

            # 3. Return Canonical Data
            resolved_assets.append(asset_data)
            
        if self.debug:
            print(f"[Resolver] Resolved {len(resolved_assets)} assets from {scan_source}")
            
        return resolved_assets
    
    def _enrich_with_static_map(self, asset_data: Dict) -> None:
        """Enrich asset with data from static IP map (fills gaps only)."""
        ip = asset_data.get('last_seen_ip')
        if ip and ip in STATIC_IP_MAP:
            for key, value in STATIC_IP_MAP[ip].items():
                if not asset_data.get(key):
                    asset_data[key] = value   