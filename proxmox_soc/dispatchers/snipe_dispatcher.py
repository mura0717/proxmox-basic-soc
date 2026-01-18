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
                
                # --- FIX: Robust Response Handling ---
                resp = None
                
                if action == 'create':
                    resp = requests.post(
                        f"{SNIPE.snipe_url}/api/v1/hardware",
                        json=payload,
                        headers=SNIPE.headers,
                        verify=SNIPE.verify_ssl,
                        timeout=30
                    )
                    
                    # Safely parse JSON
                    try:
                        body = resp.json()
                    except ValueError:
                        body = {}

                    if resp.status_code in (200, 201) and body.get('status') == 'success':
                        new_id = body['payload']['id']
                        build_result.snipe_id = new_id  # Store for downstream use
                        build_result.metadata['dispatch_ok'] = True
                        results["created"] += 1
                        if self.debug:
                            print(f"  ✓ Created: {name} (ID: {new_id})")
                    else:
                        build_result.metadata["dispatch_ok"] = False
                        results["failed"] += 1
                        if self.debug:
                            # Log raw text if JSON fails or status is error
                            err_msg = body.get('messages') or resp.text[:100]
                            print(f"  ✗ Create failed: {name} - Status: {resp.status_code} - {err_msg}")
                        
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
                        verify=SNIPE.verify_ssl,
                        timeout=30
                    )
                    
                    try:
                        body = resp.json()
                    except ValueError:
                        body = {}

                    if resp.status_code in (200, 201) and body.get('status') == 'success':
                        build_result.metadata['dispatch_ok'] = True
                        results["updated"] += 1
                        if self.debug:
                            print(f"  ✓ Updated: {name}")
                    else:
                        build_result.metadata['dispatch_ok'] = False
                        results["failed"] += 1
                        if self.debug:
                            err_msg = body.get('messages') or resp.text[:100]
                            print(f"  ✗ Update failed: {name} - Status: {resp.status_code} - {err_msg}")
            
            except Exception as e:
                build_result.metadata['dispatch_ok'] = False
                results["failed"] += 1
                if self.debug:
                    print(f"  ✗ Error: {build_result.payload.get('name', 'Unknown')} - {e}")

        print(f"[SNIPE-IT] Done: {results['created']} created, {results['updated']} updated, {results['failed']} failed")
        return results