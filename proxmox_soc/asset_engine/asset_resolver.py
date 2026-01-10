from typing import Dict, List
from proxmox_soc.config.network_config import STATIC_IP_MAP

class AssetResolver:
    def resolve(self, scan_source: str, scan_data: List[Dict]) -> List[Dict]:
        resolved_assets = []
        for asset in scan_data:
            # 1. Tag Source
            asset['_source'] = scan_source
            
            # 2. Enrich (Static IP Map)
            ip = asset.get('last_seen_ip')
            if ip and ip in STATIC_IP_MAP:
                for key, value in STATIC_IP_MAP[ip].items():
                    if not asset.get(key):
                        asset[key] = value

            # 3. Return Canonical Data
            resolved_assets.append(asset)
            
        return resolved_assets