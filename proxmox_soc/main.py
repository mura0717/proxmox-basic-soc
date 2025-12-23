#!/usr/bin/env python3
"""
Hydra / Proxmox SOC Orchestrator

Flow:
Scanner (data) -> Matcher (actions w/ canonical_data) -> Builder (snipe_payload) -> Dispatchers
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Any, Dict, List
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[2]
ENV_PATH = BASE_DIR / '.env'

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

MAIN_DEBUG = os.getenv('MAIN_DEBUG', '0') == '1'
MAIN_DRY_RUN = os.getenv('MAIN_DRY_RUN', '0') == '1'

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
    
    if MAIN_DRY_RUN:
        print("\n[DRY RUN] Skipping API Dispatch.")
        import json
        dry_run_dir = BASE_DIR / "logs" / "dry_runs"
        dry_run_dir.mkdir(parents=True, exist_ok=True)
        dry_run_file = dry_run_dir / f"dry_run_{scan_type}.json"
        with open(dry_run_file, "w") as f:
            json.dump(actions, f, indent=2, default=str)
        print(f"[DRY RUN] Payloads written to: {dry_run_file}")
        return
    
    # Snipe first so new creates get snipe_id for downstream
    snipe_results = SnipeITDispatcher().sync(actions)
    if MAIN_DEBUG:
        print(f"[SNIPE] {snipe_results}")

    if not skip_zabbix:
        zbx_results = ZabbixDispatcher().sync(actions)
        if MAIN_DEBUG:
            print(f"[ZABBIX] {zbx_results}")

    if not skip_wazuh:
        wazuh_results = WazuhDispatcher().sync(actions)
        if MAIN_DEBUG:
            print(f"[WAZUH] {wazuh_results}")
        # Wazuh dispatcher only prints if debug is on, so we might want to keep this or rely on dispatcher

def main() -> None:
    parser = argparse.ArgumentParser(description="Hydra Asset Sync Orchestrator")

    parser.add_argument("--nmap", metavar="PROFILE", help="Run Nmap scan (discovery, full, quick)")
    parser.add_argument("--ms365", action="store_true", help="Run Microsoft 365 collection")
    parser.add_argument("--all", action="store_true", help="Run Nmap (discovery) + MS365")
    
    parser.add_argument("--dry-run", action="store_true", help="Run matching+building only, do not dispatch")
    parser.add_argument("--test", action="store_true", help="Run integration tests with mock data")

    parser.add_argument("--skip-zabbix", action="store_true", help="Skip Zabbix sync")
    parser.add_argument("--skip-wazuh", action="store_true", help="Skip Wazuh logging")
    parser.add_argument("--list-profiles", action="store_true", help="List available Nmap scan profiles")

    args = parser.parse_args()

    if args.test:
        print("\n=== RUNNING INTEGRATION TESTS (MOCK DATA) ===")
        from proxmox_soc.debug.tests.test_hydra import main as run_tests
        sys.exit(run_tests())

    if args.dry_run:
        global MAIN_DRY_RUN
        MAIN_DRY_RUN = True

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