"""
Main Orchestrator for Proxmox SOC Integration

Coordinating the flow: 
Scanner (Data) -> Matcher (Action) -> Builder (Payload) -> Dispatcher (API)
"""

import argparse
from typing import List, Dict

from proxmox_soc.utils.sudo_utils import elevate_to_root
from proxmox_soc.asset_engine.asset_matcher import AssetMatcher
from proxmox_soc.builders.snipe_builder import SnipePayloadBuilder
from proxmox_soc.dispatchers.snipe_dispatcher import SnipeITDispatcher
from proxmox_soc.dispatchers.zabbix_dispatcher import ZabbixDispatcher
from proxmox_soc.dispatchers.wazuh_dispatcher import WazuhDispatcher
from proxmox_soc.scanners.nmap_scanner import NmapScanner
from proxmox_soc.scanners.ms365_aggregator import Microsoft365Aggregator

def run_pipeline(scan_type: str, assets: List[Dict], args):
    """
    The Core Pipeline: Match -> Build -> Dispatch
    """
    if not assets:
        print(f"No assets found for {scan_type}.")
        return

    # 1. MATCHING (Decide what to do)
    # Returns standardized action objects with 'canonical_data'
    print(f"--- MATCHING ({scan_type}) ---")
    matcher = AssetMatcher()
    actions = matcher.process_scan_data(scan_type, assets)

    if not actions:
        print("No actionable assets found.")
        return

    # 2. BUILDING (Format the data)
    # The orchestrator asks the Builder to transform canonical data into a Snipe-IT compatible payload.
    print(f"--- BUILDING PAYLOADS ({len(actions)}) ---")
    builder = SnipePayloadBuilder()
    
    for action in actions:
        # Transform canonical data -> Snipe-IT JSON
        payload = builder.build(action)
        # Inject payload back into the action object for dispatchers to use
        action['snipe_payload'] = payload

    # 3. DISPATCHING (Send the data)
    print("--- DISPATCHING ---")
    
    # Snipe-IT (Primary System of Record)
    SnipeITDispatcher().sync(actions)
    
    # Zabbix (Optional)
    if not args.skip_zabbix:
        ZabbixDispatcher().sync(actions)
    
    # Wazuh (Optional)
    if not args.skip_wazuh:
        WazuhDispatcher().sync(actions)

def main():
    parser = argparse.ArgumentParser(description="Hydra Asset Sync Orchestrator")
    
    # Scan Selection Arguments
    parser.add_argument("--nmap", metavar="PROFILE", help="Run Nmap scan (e.g., 'discovery', 'full')")
    parser.add_argument("--ms365", action="store_true", help="Run Microsoft 365 sync")
    
    # Dispatcher Flags
    parser.add_argument("--skip-zabbix", action="store_true", help="Skip Zabbix sync")
    parser.add_argument("--skip-wazuh", action="store_true", help="Skip Wazuh logging")
    
    args = parser.parse_args()

    # Safety check: Ensure at least one scan type is selected
    if not (args.nmap or args.ms365):
        parser.print_help()
        print("\nError: You must specify a scan type (--nmap or --ms365)")
        return

    # --- Phase 1: Nmap Scan ---
    if args.nmap:
        # Nmap requires root privileges for OS fingerprinting
        elevate_to_root()
        
        print(f"\n=== STARTING NMAP SCAN: {args.nmap} ===")
        scanner = NmapScanner()
        # Collect raw data (Scanner is dumb, just returns list)
        assets = scanner.collect_assets(args.nmap)
        # Run the processing pipeline
        run_pipeline("nmap", assets, args)

    # --- Phase 2: Microsoft 365 Sync ---
    if args.ms365:
        print("\n=== STARTING MS365 SYNC ===")
        # MS365 doesn't need root, but if we elevated for Nmap, we stay elevated.
        aggregator = Microsoft365Aggregator()
        # Collect raw data
        assets = aggregator.collect_assets()
        # Run the processing pipeline
        run_pipeline("microsoft365", assets, args)

if __name__ == "__main__":
    main()