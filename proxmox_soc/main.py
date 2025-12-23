#!/usr/bin/env python3
"""
Hydra / Proxmox SOC Orchestrator

Flow:
Scanner (data) -> Matcher (actions w/ canonical_data) -> Builder (snipe_payload) -> Dispatchers
"""

import argparse
from typing import Any, Dict, List


def run_pipeline(scan_type: str, assets: List[Dict[str, Any]], *, skip_zabbix: bool, skip_wazuh: bool) -> None:
    if not assets:
        print(f"No assets found for {scan_type}.")
        return

    # Import here to keep startup light and avoid importing unused deps
    from proxmox_soc.asset_engine.asset_matcher import AssetMatcher
    from proxmox_soc.builders.snipe_builder import SnipePayloadBuilder
    from proxmox_soc.dispatchers.snipe_dispatcher import SnipeITDispatcher
    from proxmox_soc.dispatchers.zabbix_dispatcher import ZabbixDispatcher
    from proxmox_soc.dispatchers.wazuh_dispatcher import WazuhDispatcher

    print(f"\n=== MATCHING ({scan_type}) ===")
    matcher = AssetMatcher()  # fresh per scan type = avoids stale caches
    actions = matcher.process_scan_data(scan_type, assets)

    if not actions:
        print("No actionable assets found.")
        return

    print(f"\n=== BUILDING SNIPE PAYLOADS ({len(actions)}) ===")
    builder = SnipePayloadBuilder()
    for action in actions:
        # Your builder expects an action object
        action["snipe_payload"] = builder.build(action)

    print("\n=== DISPATCHING ===")
    # Snipe first so new creates get snipe_id for downstream
    snipe_results = SnipeITDispatcher().sync(actions)
    print(f"[SNIPE] {snipe_results}")

    if not skip_zabbix:
        zbx_results = ZabbixDispatcher().sync(actions)
        print(f"[ZABBIX] {zbx_results}")

    if not skip_wazuh:
        wazuh_results = WazuhDispatcher().sync(actions)
        print(f"[WAZUH] {wazuh_results}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Hydra Asset Sync Orchestrator")

    parser.add_argument("--nmap", metavar="PROFILE", help="Run Nmap scan (discovery, full, quick)")
    parser.add_argument("--ms365", action="store_true", help="Run Microsoft 365 collection")
    parser.add_argument("--all", action="store_true", help="Run Nmap (discovery) + MS365")

    parser.add_argument("--skip-zabbix", action="store_true", help="Skip Zabbix sync")
    parser.add_argument("--skip-wazuh", action="store_true", help="Skip Wazuh logging")
    parser.add_argument("--list-profiles", action="store_true", help="List available Nmap scan profiles")

    args = parser.parse_args()

    if args.list_profiles:
        from proxmox_soc.config.nmap_profiles import NMAP_SCAN_PROFILES
        print("\nAvailable Nmap scan profiles:")
        for name, cfg in NMAP_SCAN_PROFILES.items():
            print(f"  {name:12} - {cfg.get('description','')}")
        return

    if not any([args.nmap, args.ms365, args.all]):
        parser.print_help()
        return

    # Nmap
    if args.all or args.nmap:
        from proxmox_soc.utils.sudo_utils import elevate_to_root
        from proxmox_soc.scanners.nmap_scanner import NmapScanner

        profile = "discovery" if args.all else args.nmap
        elevate_to_root()
        nmap_assets = NmapScanner().collect_assets(profile)
        run_pipeline("nmap", nmap_assets, skip_zabbix=args.skip_zabbix, skip_wazuh=args.skip_wazuh)

    # MS365
    if args.all or args.ms365:
        from proxmox_soc.scanners.ms365_aggregator import Microsoft365Aggregator

        ms365_assets = Microsoft365Aggregator().collect_assets()
        run_pipeline("microsoft365", ms365_assets, skip_zabbix=args.skip_zabbix, skip_wazuh=args.skip_wazuh)


if __name__ == "__main__":
    main()