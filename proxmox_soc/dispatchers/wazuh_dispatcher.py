"""
Wazuh Dispatcher Module"""

import os
import json
from proxmox_soc.config.hydra_settings import WAZUH
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher
from proxmox_soc.builders.wazuh_builder import WazuhPayloadBuilder
from proxmox_soc.states.wazuh_state import WazuhStateManager

class WazuhDispatcher(BaseDispatcher):
    def __init__(self):
        self.builder = WazuhPayloadBuilder()
        self.state = WazuhStateManager(WAZUH.state_file)
        self.debug = os.getenv('WAZUH_DISPATCHER_DEBUG', '0') == '1'

    def sync(self, assets: list) -> dict:
        results = {"created": 0, "updated": 0, "skipped": 0, "failed":0}
        print(f"\n[WAZUH] Processing {len(assets)} assets...")
        
        WAZUH.event_log.parent.mkdir(parents=True, exist_ok=True)

        with open(WAZUH.event_log, 'a') as f:
            for asset in assets:
                canonical_data = asset.get("canonical_data", {})
                # 1. Ask State Manager what to do
                action, asset_id = self.state.process_asset(canonical_data)
                
                if action == 'skip':
                    results['skipped'] += 1
                    continue
                # 2. Build Event
                try:
                    log_entry = self.builder.build_event(asset, asset_id, action)
                    f.write(json.dumps(log_entry) + "\n")
                    results[action + 'd'] += 1
                    if self.debug:
                        print(f"  ✓ {action} event for: {asset['canonical_data'].get('name', 'Unknown')}")
                except Exception as e:
                    results["failed"] += 1
                    if self.debug:
                        print(f"  ✗ Failed {action} event for: {asset['canonical_data'].get('name', 'Unknown')} - Error: {e}")
        
        # Persist state changes to disk
        self.state.save()

        if self.debug:
            print(f"  ✓ Logged {results['created']} created, {results['updated']} updated, {results['skipped']} skipped, and {results['failed']} failed events.")
        return results