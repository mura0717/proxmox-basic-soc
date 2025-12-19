"""Main module for Proxmox SOC integration."""

import json
import os

from proxmox_soc.asset_engine.asset_matcher import AssetMatcher
from proxmox_soc.dispatchers.snipe_dispatcher import SnipeITDispatcher
from proxmox_soc.dispatchers.zabbix_dispatcher import ZabbixDispatcher
from proxmox_soc.dispatchers.wazuh_dispatcher import WazuhDispatcher

def main():
    SCAN_FILE = "/opt/diabetes/proxmox-basic-soc/output/test_scan.json"
    if not os.path.exists(SCAN_FILE): return
    with open(SCAN_FILE, 'r') as f: scan_data = json.load(f)

    # 1. Processing
    print("--- 1. PROCESSING ---")
    matcher = AssetMatcher()
    actions = matcher.process_scan_data("nmap", scan_data.get('nmap', []))

    # 2. Dispatching
    print("\n--- 2. DISPATCHING ---")
    SnipeITDispatcher().sync(actions)
    ZabbixDispatcher().sync(actions)
    WazuhDispatcher().sync(actions)

if __name__ == "__main__":
    main()