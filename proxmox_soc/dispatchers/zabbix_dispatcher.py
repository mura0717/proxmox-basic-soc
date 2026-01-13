"""
Zabbix Dispatcher Module
"""

import os
import requests
from typing import List, Dict

from proxmox_soc.config.hydra_settings import ZABBIX
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher
from proxmox_soc.builders.base_builder import BuildResult


class ZabbixDispatcher(BaseDispatcher):
    """Dispatches hosts to Zabbix via JSON-RPC API."""
    
    def __init__(self):
        self.auth = None
        self.req_id = 0
        self.debug = os.getenv('ZABBIX_DISPATCHER_DEBUG', '0') == '1'
        self._group_cache: Dict[str, str] = {}
        self._authenticate()

    def _authenticate(self) -> bool:
        """Authenticate with Zabbix API."""
        try:
            self.auth = self._rpc("user.login", {
                "username": ZABBIX.zabbix_username,
                "password": ZABBIX.zabbix_pass
            })
            return True
        except Exception as e:
            print(f"[ZABBIX] Authentication failed: {e}")
            return False
    
    def _rpc(self, method: str, params: Dict) -> Dict:
        """Make JSON-RPC call to Zabbix."""
        self.req_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.req_id
        }
        if self.auth:
            payload['auth'] = self.auth
        
        resp = requests.post(ZABBIX.zabbix_url, json=payload, verify=False, timeout=30)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise RuntimeError(f"Zabbix API error: {data['error']}")

        return data.get("result")

    def sync(self, build_results: List[BuildResult]) -> Dict[str, int]:
        """Sync built payloads to Zabbix."""
        results = {"created": 0, "updated": 0, "skipped": 0, "failed": 0}
        print(f"\n[ZABBIX] Syncing {len(build_results)} hosts...")
        
        if not self.auth:
            print("[ZABBIX] Not authenticated. Skipping all.")
            results["failed"] = len(build_results)
            return results

        for build_result in build_results:
            try:
                status = self._sync_host(build_result)
                results[status] += 1
                if self.debug:
                    name = build_result.payload.get('name', 'Unknown')
                    print(f"  ✓ {status}: {name}")
            except Exception as e:
                results["failed"] += 1
                if self.debug:
                    print(f"  ✗ Error: {e}")

        print(f"[ZABBIX] Done: {results['created']} created, {results['updated']} updated, "
              f"{results['skipped']} skipped, {results['failed']} failed")
        return results

    def _sync_host(self, build_result: BuildResult) -> str:
        """Sync single host. Returns status string."""
        payload = build_result.payload
        
        # Skip if no IP
        if not payload.get('interfaces', [{}])[0].get('ip'):
            return "skipped"
        
        # Resolve group name to ID
        group_name = build_result.metadata.get('group_name', 'Discovered hosts')
        group_id = self._get_or_create_group(group_name)
        payload['groups'] = [{"groupid": group_id}]
        
        # Check if host exists
        existing = self._rpc("host.get", {"filter": {"host": [payload['host']]}})
        
        if existing:
            # Update existing
            host_id = existing[0]['hostid']
            update_payload = {**payload, "hostid": host_id}
            del update_payload['groups']  # Can't update groups this way
            self._rpc("host.update", update_payload)
            return "updated"
        else:
            # Create new
            self._rpc("host.create", payload)
            return "created"

    def _get_or_create_group(self, group_name: str) -> str:
        """Get group ID, creating if necessary."""
        if group_name in self._group_cache:
            return self._group_cache[group_name]
        
        groups = self._rpc("hostgroup.get", {
            "filter": {"name": [group_name]},
            "output": ["groupid"]
        })
        
        if groups:
            group_id = groups[0]['groupid']
        else:
            result = self._rpc("hostgroup.create", {"name": group_name})
            group_id = result['groupids'][0]
        
        self._group_cache[group_name] = group_id
        return group_id