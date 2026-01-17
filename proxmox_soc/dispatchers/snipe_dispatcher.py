"""
Snipe-IT Dispatcher Module
"""

import os
import requests
from typing import List, Dict

from proxmox_soc.config.hydra_settings import SNIPE
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher
from proxmox_soc.builders.base_builder import BuildResult


class SnipeDispatcher(BaseDispatcher):
    """Dispatches assets to Snipe-IT API."""
    
    def __init__(self):
        self.debug = os.getenv('SNIPE_DISPATCHER_DEBUG', '0') == '1'
        
    def sync(self, build_results: List[BuildResult]) -> Dict[str, int]:
        """Sync built payloads to Snipe-IT."""
        results = {"created": 0, "updated": 0, "failed": 0}
        print(f"\n[SNIPE-IT] Syncing {len(build_results)} assets...")
        
        for build_result in build_results:
            try:
                payload = build_result.payload
                name = payload.get('name', 'Unknown')
                action = build_result.action
                
                if action == 'create':
                    resp = requests.post(
                        f"{SNIPE.snipe_url}/api/v1/hardware",
                        json=payload,
                        headers=SNIPE.headers,
                        verify=SNIPE.verify_ssl
                    )
                    if resp.status_code == 200 and resp.json().get('status') == 'success':
                        new_id = resp.json()['payload']['id']
                        build_result.snipe_id = new_id  # Store for downstream use
                        build_result.metadata['dispatch_ok'] = True
                        results["created"] += 1
                        if self.debug:
                            print(f"  ✓ Created: {name} (ID: {new_id})")
                    else:
                        build_result.metadata["dispatch_ok"] = False
                        results["failed"] += 1
                        if self.debug:
                            print(f"  ✗ Create failed: {name} - {resp.text[:100]}")
                        
                elif action == 'update':
                    if not build_result.snipe_id:
                        build_result.metadata['dispatch_ok'] = False
                        results["failed"] += 1
                        if self.debug:
                            print(f"  ✗ Update skipped (missing snipe_id): {name}")
                        continue
                    resp = requests.patch(
                        f"{SNIPE.snipe_url}/api/v1/hardware/{build_result.snipe_id}",
                        json=payload,
                        headers=SNIPE.headers,
                        verify=SNIPE.verify_ssl
                    )
                    if resp.status_code == 200:
                        build_result.metadata['dispatch_ok'] = True
                        results["updated"] += 1
                        if self.debug:
                            print(f"  ✓ Updated: {name}")
                    else:
                        build_result.metadata['dispatch_ok'] = False
                        results["failed"] += 1
                        if self.debug:
                            print(f"  ✗ Update failed: {name}")
            
            except Exception as e:
                build_result.metadata['dispatch_ok'] = False
                results["failed"] += 1
                if self.debug:
                    print(f"  ✗ Error: {build_result.payload.get('name', 'Unknown')} - {e}")

        print(f"[SNIPE-IT] Done: {results['created']} created, {results['updated']} updated, {results['failed']} failed")
        return results