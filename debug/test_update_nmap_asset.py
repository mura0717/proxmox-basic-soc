"""
Test single Nmap asset UPDATE synchronization via Asset Matcher to Snipe-IT.
This script is designed to debug the update workflow for an existing asset.
"""

import os
import sys
from pprint import pprint
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets_sync_library.asset_matcher import AssetMatcher

# Set the ID of the Snipe-IT asset to test the update against.
ASSET_ID_TO_TEST = 612  # <--- CHANGE THIS TO A REAL ASSET ID

# New Nmap scan data that should trigger a re-categorization.
NEW_NMAP_DATA = {
    "last_seen_ip": "192.168.1.64",
    "nmap_last_scan": "2025-11-20T10:00:00.000000+00:00",
    "nmap_scan_profile": "discovery",
    "name": "ap7-reception.diabetes.local",  # This hostname is key for categorization
    "dns_hostname": "ap7-reception.diabetes.local",
    "_source": "nmap",
    "mac_addresses": "D0:21:F9:C7:97:E7",
    "manufacturer": "Ubiquiti Networks",
    "nmap_open_ports": "22/tcp/ssh ( )\n8080/tcp/http-proxy ( )",
    "open_ports_hash": "d374ef4e815def6c253e48ccae9a36dc",
    "nmap_services": ["ssh", "http-proxy"],
    "first_seen_date": "2025-11-19T11:06:54.121518+00:00"
}

def main():
    """
    Runs the update test against a single, specified asset.
    """
    if ASSET_ID_TO_TEST == 0:
        print("ERROR: Please set the ASSET_ID_TO_TEST variable in this script.")
        sys.exit(1)

    print(f"--- Starting Update Test for Asset ID: {ASSET_ID_TO_TEST} ---")

    matcher = AssetMatcher()
    matcher.debug = True

    # Fetch the existing asset data from Snipe-IT
    print("\n[DEBUG] Fetching existing asset data from Snipe-IT...")
    existing_asset = matcher.asset_service.get_by_id(ASSET_ID_TO_TEST)
    if not existing_asset:
        print(f"ERROR: Could not find asset with ID {ASSET_ID_TO_TEST} in Snipe-IT.")
        sys.exit(1)

    print(f"  > Found asset: '{existing_asset.get('name')}'")
    print(f"  > Current Category: {existing_asset.get('category', {}).get('name', 'N/A')}")

    # Simulate the main processing loop for a single update
    print("\n[DEBUG] Simulating asset update process...")

    # Manually merge data, bypassing asset finding to force an update on the fetched asset.
    flattened_existing = {**existing_asset}
    if isinstance(flattened_existing.get('model'), dict):
        flattened_existing['model'] = flattened_existing['model'].get('name')
    if isinstance(flattened_existing.get('manufacturer'), dict):
        flattened_existing['manufacturer'] = flattened_existing['manufacturer'].get('name')

    merged_data = matcher.merge_asset_data({'_source': 'existing', **flattened_existing}, NEW_NMAP_DATA)
    merged_data['_source'] = 'nmap' # Ensure new source is prioritized for categorization

    # Remove the old category from the merged data to force re-categorization on update.
    merged_data.pop('category', None)

    print("\n[DEBUG] --- DATA AFTER MERGE ---")
    print(f"[DEBUG] Merged data contains {len(merged_data)} keys. Preparing to build final payload.")
    # Call the internal update method directly to test the payload generation and API call.
    matcher._update_asset(ASSET_ID_TO_TEST, merged_data, 'nmap')

    print(f"\n--- Test for Asset ID: {ASSET_ID_TO_TEST} Complete ---")
    print("Check the console output above to see the merge logic and final payload.")

if __name__ == "__main__":
    main()
