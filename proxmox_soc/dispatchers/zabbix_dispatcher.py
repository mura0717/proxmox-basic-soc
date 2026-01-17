"""
Zabbix Dispatcher Module
"""

import os
import json
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
                # 1. Validation: Skip if no IP
                new_ip = item.payload.get('interfaces', [{}])[0].get('ip')
                
                if not new_ip:
                    results['skipped'] += 1
                    if self.debug:
                        print(f"  ⊘ Skipped (no IP): {item.payload.get('name', 'Unknown')}")
                    continue
                
                # 2. Validation: Host Group
                group_name = item.metadata.get('group_name')
                group_id = self._get_or_create_group(group_name)
                
                if not group_id:
                    results['failed'] += 1
                    if self.debug:
                        print(f"  ✗ Failed (no group): {item.payload.get('name', 'Unknown')}")
                    continue
                    
                item.payload['groups'] = [{"groupid": group_id}]
                
                # 3. Action: Update
                if item.action == 'update':
                    hostid = item.metadata.get('hostid')
                    
                    if not hostid:
                        results['failed'] += 1
                        if self.debug:
                            print(f"  ✗ Update failed (no hostid): {item.payload.get('name', 'Unknown')}")
                        continue
                    
                    # A. Update Basic Info (Inventory, Tags, Name)
                    update_payload = {
                        "hostid": hostid,
                        "inventory": item.payload['inventory'],
                        "tags": item.payload['tags']
                    }
                    self.client.call("host.update", update_payload)
                    
                    # B. Update IP Address (The logic you added)
                    if new_ip:
                        try:
                            # Fetch existing interfaces for this host
                            interfaces = self.client.call("hostinterface.get", {
                                "hostids": hostid,
                                "output": ["interfaceid", "ip"]
                            })
                            
                            # We assume the first interface is the primary agent interface
                            if interfaces:
                                main_interface = interfaces[0]
                                if main_interface.get('ip') != new_ip:
                                    self.client.call("hostinterface.update", {
                                        "interfaceid": main_interface['interfaceid'],
                                        "ip": new_ip
                                    })
                                    if self.debug:
                                        print(f"    ↻ Updated IP: {main_interface['ip']} → {new_ip}")
                        except Exception as e:
                            if self.debug:
                                print(f"    ⚠️ Could not update interface IP: {e}")

                    results['updated'] += 1
                    if self.debug:
                        print(f"  ✓ Updated: {item.payload.get('name')} (ID: {hostid})")
                        
                # 4. Action: Create
                else: 
                    result = self.client.call("host.create", item.payload)
                    results['created'] += 1
                    
                    if self.debug:
                        new_id = result.get('hostids', ['?'])[0] if result else '?'
                        print(f"  ✓ Created: {item.payload.get('name')} (ID: {new_id})")
                        
            except Exception as e:
                results['failed'] += 1
                if self.debug:
                    print(f"  ✗ Error: {item.payload.get('name', 'Unknown')} - {e}")
                    
        if self.debug and build_results:
            last_payload = build_results[-1].payload if build_results else {}
            print(f"  LOG (last): {json.dumps(last_payload, default=str)[:100]}...")
                    
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