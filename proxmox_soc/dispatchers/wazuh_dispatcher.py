"""
Wazuh Dispatcher Module
"""

import os
import json
from typing import List, Dict

from proxmox_soc.config.hydra_settings import WAZUH
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher
from proxmox_soc.builders.base_builder import BuildResult

class WazuhDispatcher(BaseDispatcher):
    """Dispatches events to Wazuh log file."""
    
    def __init__(self):
        self.debug = os.getenv('WAZUH_DISPATCHER_DEBUG', '0') == '1'

    def sync(self, build_results: List[BuildResult]) -> Dict[str, int]:
        """Write built events to Wazuh log file."""
        results = {"created": 0, "updated": 0, "failed": 0}
        print(f"\n[WAZUH] Writing {len(build_results)} events...")
        
        WAZUH.event_log.parent.mkdir(parents=True, exist_ok=True)

        with open(WAZUH.event_log, 'a') as f:
            for build_result in build_results:
                try:
                    f.write(json.dumps(build_result.payload) + "\n")
                    build_result.metadata['dispatch_ok'] = True
                    if build_result.action == 'create':
                        results["created"] += 1
                    else:
                        results["updated"] += 1
                        
                    if self.debug:
                        name = build_result.payload.get('asset', {}).get('name', 'Unknown')
                        print(f"  ✓ {build_result.action}: {name}")
                        
                except Exception as e:
                    results["failed"] += 1
                    build_result.metadata["dispatch_ok"] = False
                    if self.debug:
                        print(f"  ✗ Failed to write event: {e}")

        print(f"[WAZUH] Done: {results['created']} created, {results['updated']} updated, {results['failed']} failed")
        return results