"""
Zabbix Dispatcher Module
"""

import os
import requests
from typing import List, Dict, Any, Optional

from proxmox_soc.config.hydra_settings import ZABBIX
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher
from proxmox_soc.builders.zabbix_builder import ZabbixPayloadBuilder

class ZabbixDispatcher(BaseDispatcher):
    def __init__(self):
        self.auth = None
        self.req_id = 0
        self.builder = ZabbixPayloadBuilder()
        self.authenticated = self.authenticate()
        self.debug = os.getenv('ZABBIX_DISPATCHER_DEBUG', '0') == '1'

    def authenticate(self) -> bool:
        try:
            self.auth = self._rpc("user.login", {"username": ZABBIX.zabbix_username, "password": ZABBIX.zabbix_pass})
            return True
        except Exception as e:
            print(f"Zabbix authentication failed: {e}")
            return False
    
    def _rpc(self, method, params):
        self.req_id += 1
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": self.req_id}
        if self.auth: payload['auth'] = self.auth
        result = requests.post(ZABBIX.zabbix_url, json=payload, verify=False, timeout=30).json().get('result')
        if 'error' in result:
            raise RuntimeError(f"Zabbix API error: {result['error']}")
        return result 
    
    def sync(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        results = {"created": 0, "updated": 0, "skipped": 0, "failed": 0}
        print(f"\n[ZABBIX] Syncing {len(assets)} assets...")
        
        if self.authenticated:
            for asset in assets:
                try:
                    status = self._sync_asset(asset)
                    results[status] += 1
                    if self.debug:
                        print(f"  ✓ Status: {status}")
                except Exception as e:
                    results["failed"] += 1
                    if self.debug:
                        print(f"  ✗ Error: {e}")
        else:
            print("Zabbix authentication failed. Cannot sync assets.")
            results["failed"] = len(assets)
            
        print(f"[ZABBIX] Done: {results['created']} created, {results['updated']} updated, {results['skipped']} skipped, {results['failed']} failed")
        return results
    
    def _sync_asset(self, asset: Dict[str, Any]) -> str:
        """Sync single asset. Returns 'created', 'updated', 'skipped', or 'failed'."""
        canonical = asset.get('canonical_data', {})
        ip = canonical.get('last_seen_ip')
        
        if not ip:
            return "skipped"
        
        # 1. Use Builder logic
        dt = canonical.get('device_type')
        group_name = self.builder.get_group_name(dt)
        
        # 2. Network Check (Dispatcher Logic)
        group_check = self._rpc("hostgroup.get", {"filter": {"name": [group_name]}, "output": ["groupid"]})
        if group_check: group_id = group_check[0]['groupid']
        else: group_id = self._rpc("hostgroup.create", {"name": group_name})['groupids'][0]

        # 3. Build Payload
        host_payload = self.builder.build_host(asset, group_id)
        
        # 4. Transmit
        existing = self._rpc("host.get", {"filter": {"host": [host_payload['host']]}})
        if not existing:
            self._rpc("host.create", host_payload)
            if self.debug:
                print(f"  ✓ Created Host: {host_payload['name']}")
            return "created"
        
        return "skipped"
