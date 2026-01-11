"""
Asset Resolver
Enriches and normalizes scan data into canonical format.
"""

import os
from dataclasses import dataclass
from typing import Dict, List

from proxmox_soc.config.network_config import STATIC_IP_MAP
from proxmox_soc.debug.tools.asset_debug_logger import debug_logger


@dataclass
class ResolvedAsset:
    """An asset with its canonical data after enrichment."""
    canonical_data: Dict
    source: str


class AssetResolver:
    """
    Central coordinator for asset data processing.
    
    Responsibilities:
    - Data enrichment (static IP mappings)
    - Source tagging
    - Debug logging
    """
    
    def __init__(self):
        self.debug = os.getenv('ASSET_RESOLVER_DEBUG', '0') == '1'
        
    def resolve(self, scan_source: str, scan_data: List[Dict]) -> List[ResolvedAsset]:
        """
        Process raw scan data into resolved assets.
        
        Args:
            scan_source: Source of the scan ('nmap', 'microsoft365', etc.)
            scan_data: Raw asset data from scanner
            
        Returns:
            List of ResolvedAsset objects
        """
        resolved_assets = []
        
        for asset_data in scan_data:
            # 1. Tag Source
            asset_data['_source'] = scan_source
            
            # 2. Enrich with static mappings
            self._enrich_with_static_map(asset_data)
            
            # 3. Debug logging
            if self.debug:
                debug_logger.log_parsed_asset_data(scan_source, asset_data)
            
            # 4. Create ResolvedAsset
            resolved_assets.append(ResolvedAsset(
                canonical_data=asset_data,
                source=scan_source
            ))
            
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