"""
Snipe-IT Dispatcher Module
"""
import requests
from proxmox_soc.config.settings import SNIPE
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher

class SnipeITDispatcher(BaseDispatcher):
    def sync(self, assets: list):
        print(f"\n[SNIPE-IT] Syncing {len(assets)} assets...")
        for asset in assets:
            try:
                payload = asset['snipe_payload']
                if asset['action'] == 'create':
                    resp = requests.post(f"{SNIPE.snipe_url}/api/v1/hardware", json=payload, headers=SNIPE.headers, verify=SNIPE.verify_ssl)
                    if resp.status_code == 200 and resp.json().get('status') == 'success':
                        new_id = resp.json()['payload']['id']
                        asset['snipe_id'] = new_id 
                        print(f"  ✓ Created: {payload.get('name')} (ID: {new_id})")
                elif asset['action'] == 'update' and asset['snipe_id']:
                    resp = requests.patch(f"{SNIPE.snipe_url}/api/v1/hardware/{asset['snipe_id']}", json=payload, headers=SNIPE.headers, verify=SNIPE.verify_ssl)
                    if resp.status_code == 200:
                        print(f"  ✓ Updated: {payload.get('name')}")
            except Exception as e:
                print(f"  [!] Snipe Error: {e}")
        return assets