"""
Zabbix Dispatcher Module
"""

import os
from typing import List, Dict

from proxmox_soc.zabbix.zabbix_api.zabbix_client import ZabbixClient
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher
from proxmox_soc.builders.base_builder import BuildResult

class ZabbixDispatcher(BaseDispatcher):
    """Dispatches hosts to Zabbix via JSON-RPC API."""
    
    def __init__(self):
        self.debug = os.getenv('ZABBIX_DISPATCHER_DEBUG', '0') == '1'
        self._group_cache: Dict[str, str] = {}
        self.client = ZabbixClient()

    def sync(self, build_results: List[BuildResult]) -> Dict[str, int]:
        """Sync built payloads to Zabbix."""
        results = {"created": 0, "updated": 0, "skipped": 0, "failed": 0}
        print(f"\n[ZABBIX] Syncing {len(build_results)} hosts...")
        
        if not self.client.auth:
            print("[ZABBIX] Not authenticated. Skipping all.")
            results["failed"] = len(build_results)
            return results

        for item in build_results:
            try:
                # Resolve Group
                group_name = item.metadata.get('group_name')
                group_id = self._get_or_create_group(group_name)
                item.payload['groups'] = [{"groupid": group_id}]
                
                if item.action == 'update':
                    hostid = item.metadata.get('hostid')
                    if hostid:
                        update_payload = {
                            "hostid": hostid,
                            "inventory": item.payload['inventory'],
                            "tags": item.payload['tags']
                        }
                        self.client.call("host.update", update_payload)
                        results['updated'] += 1
                else:
                    self.client.call("host.create", item.payload)
                    results['created'] += 1
                    
            except Exception as e:
                results['failed'] += 1
                if self.debug: print(f"Zabbix Error: {e}")

        print(f"[ZABBIX] Done: {results['created']} created, {results['updated']} updated, "
              f"{results['skipped']} skipped, {results['failed']} failed")
        return results

    def _get_or_create_group(self, name):
        if name in self._group_cache: return self._group_cache[name]
        try:
            groups = self.client.call("hostgroup.get", {"filter": {"name": [name]}, "output": ["groupid"]})
            if groups: gid = groups[0]['groupid']
            else: gid = self.client.call("hostgroup.create", {"name": name})['groupids'][0]
            self._group_cache[name] = gid
            return gid
        except Exception as e:
            if self.debug:
                print(f"[ZABBIX] ✗ Group '{name}' get or create error: {e}")
            return None