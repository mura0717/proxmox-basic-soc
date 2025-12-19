"""
Zabbix Dispatcher Module
"""

import requests
from proxmox_soc.config.settings import ZABBIX
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher
from proxmox_soc.builders.zabbix_builder import ZabbixPayloadBuilder

class ZabbixDispatcher(BaseDispatcher):
    def __init__(self):
        self.auth = None
        self.req_id = 0
        self.builder = ZabbixPayloadBuilder() # Clean

    def _rpc(self, method, params):
        self.req_id += 1
        payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": self.req_id}
        if self.auth: payload['auth'] = self.auth
        return requests.post(ZABBIX.zabbix_url, json=payload, verify=False).json().get('result')

    def sync(self, assets: list):
        print(f"\n[ZABBIX] Syncing assets...")
        self.auth = self._rpc("user.login", {"username": ZABBIX.zabbix_username, "password": ZABBIX.zabbix_pass})
        
        for asset in assets:
            # 1. Use Builder logic
            dt = asset['canonical_data'].get('device_type')
            group_name = self.builder.get_group_name(dt)
            
            # 2. Network Check (Dispatcher Logic)
            group_check = self._rpc("hostgroup.get", {"filter": {"name": [group_name]}, "output": ["groupid"]})
            if group_check: group_id = group_check[0]['groupid']
            else: group_id = self._rpc("hostgroup.create", {"name": group_name})['groupids'][0]

            # 3. Build Payload
            host_payload = self.builder.build_host(asset, group_id)
            if not host_payload['interfaces'][0]['ip']: continue # Skip no IP

            # 4. Transmit
            existing = self._rpc("host.get", {"filter": {"host": [host_payload['host']]}})
            if not existing:
                self._rpc("host.create", host_payload)
                print(f"  ✓ Created Host: {host_payload['name']}")