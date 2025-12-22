"""
Wazuh Dispatcher Module"""

import os
import json
from proxmox_soc.config.settings import WAZUH
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher
from proxmox_soc.builders.wazuh_builder import WazuhPayloadBuilder

class WazuhDispatcher(BaseDispatcher):
    def __init__(self):
        self.builder = WazuhPayloadBuilder()
        self.debug = os.getenv('WAZUH_DISPATCHER_DEBUG', '0') == '1'

    def sync(self, assets: list):
        results = {"written": 0, "failed": 0}
        print(f"\n[WAZUH] Logging events to {WAZUH.event_log}...")
        
        WAZUH.event_log.parent.mkdir(parents=True, exist_ok=True)

        with open(WAZUH.event_log, 'a') as f:
            for asset in assets:
                log_entry = self.builder.build_event(asset)
                f.write(json.dumps(log_entry) + "\n")
        print(f"  ✓ Logged {len(assets)} events.")