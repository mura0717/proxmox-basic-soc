"""
Snipe-IT Dispatcher Module
"""

import os
import requests
from typing import List, Dict, Any

from proxmox_soc.config.settings import SNIPE
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher

class SnipeITDispatcher(BaseDispatcher):
    
    def __init__(self):
        self.debug = os.getenv('SNIPEIT_DISPATCHER_DEBUG', '0') == '1'
        
    def sync(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        results = {"created": 0, "updated": 0, "failed": 0}
        print(f"\n[SNIPE-IT] Syncing {len(assets)} assets...")
        
        for asset in assets:
            try:
                payload = asset['snipe_payload']
                name = payload.get('name', 'Unknown')
                
                if asset['action'] == 'create':
                    resp = requests.post(f"{SNIPE.snipe_url}/api/v1/hardware", json=payload, headers=SNIPE.headers, verify=SNIPE.verify_ssl)
                    if resp.status_code == 200 and resp.json().get('status') == 'success':
                        new_id = resp.json()['payload']['id']
                        asset['snipe_id'] = new_id
                        results["created"] += 1
                        if self.debug:
                            print(f"  ✓ Created: {name} (ID: {new_id})")
                    else:
                        results["failed"] += 1
                        print(f"  ✗ Create failed: {name} - {resp.text[:100]}")
                        
                elif asset['action'] == 'update' and asset['snipe_id']:
                    resp = requests.patch(f"{SNIPE.snipe_url}/api/v1/hardware/{asset['snipe_id']}", json=payload, headers=SNIPE.headers, verify=SNIPE.verify_ssl)
                    if resp.status_code == 200:
                        results["updated"] += 1
                        if self.debug:
                            print(f"  ✓ Updated: {name}")
                    else:
                        results["failed"] += 1
                        print(f"  ✗ Update failed: {name}")
            
            except Exception as e:
                results["failed"] += 1
                print(f"  ✗ Error: {asset.get('snipe_payload', {}).get('name', 'Unknown')} - {e}")
        
        print(f"[SNIPE-IT] Done: {results['created']} created, {results['updated']} updated, {results['failed']} failed")
        return assets