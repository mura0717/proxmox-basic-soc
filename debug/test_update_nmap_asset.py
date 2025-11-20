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

# --- CONFIGURATION: CHOOSE ONE IDENTIFIER ---
# Use the Asset ID, Asset Tag, OR Serial Number to find the asset you want to test.
ASSET_ID_TO_TEST = 0  # Option 1: Direct Asset ID (e.g., 612)
ASSET_TAG_TO_TEST = "AUTO-20251120155422-BDF3DA"  # Option 2: Asset Tag (e.g., "My-Asset-123")
ASSET_SERIAL_TO_TEST = "" # Option 3: Serial Number

# New Nmap scan data that should trigger a re-categorization.
NEW_NMAP_DATA = {
    "last_seen_ip": "192.168.1.176",
    "nmap_last_scan": "2025-11-20T16:22:28.182327+00:00",
    "nmap_scan_profile": "discovery",
    "name": "Device-192.168.1.176",
    "_source": "nmap",
    "mac_addresses": "D0:39:EA:23:D0:59",
    "manufacturer": "NetApp",
    "nmap_open_ports": "443/tcp/https ( )\n8443/tcp/https-alt ( )",
    "open_ports_hash": "d22b17c7a9350ec8a54d0afe47097600",
    "nmap_services": [
      "https",
      "https-alt"
    ],
    "first_seen_date": "2025-11-20T16:22:28.182359+00:00"
}

def main():
    """
    Runs the update test against a single, specified asset.
    """
    if not ASSET_ID_TO_TEST and not ASSET_TAG_TO_TEST and not ASSET_SERIAL_TO_TEST:
        print("ERROR: Please set one of ASSET_ID_TO_TEST, ASSET_TAG_TO_TEST, or ASSET_SERIAL_TO_TEST.")
        sys.exit(1)

    matcher = AssetMatcher()
    matcher.debug = True

    # Fetch the existing asset data from Snipe-IT
    print("\n[DEBUG] Fetching existing asset data from Snipe-IT...")
    existing_asset = None
    if ASSET_ID_TO_TEST:
        print(f"  -> Searching by Asset ID: {ASSET_ID_TO_TEST}")
        existing_asset = matcher.asset_service.get_by_id(ASSET_ID_TO_TEST)
    elif ASSET_TAG_TO_TEST:
        print(f"  -> Searching by Asset Tag: '{ASSET_TAG_TO_TEST}'")
        existing_asset = matcher.asset_service.search_by_asset_tag(ASSET_TAG_TO_TEST)
    elif ASSET_SERIAL_TO_TEST:
        print(f"  -> Searching by Serial Number: '{ASSET_SERIAL_TO_TEST}'")
        existing_asset = matcher.asset_service.search_by_serial(ASSET_SERIAL_TO_TEST)

    if not existing_asset:
        print(f"ERROR: Could not find the specified asset in Snipe-IT.")
        sys.exit(1)

    asset_id = existing_asset['id']
    print(f"\n--- Starting Update Test for Asset ID: {asset_id} ---")
    print(f"  > Found asset: '{existing_asset.get('name')}'")
    print(f"  > Current Category: {existing_asset.get('category', {}).get('name', 'N/A')}")
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
    matcher._update_asset(asset_id, merged_data, 'nmap')

    print(f"\n--- Test for Asset ID: {asset_id} Complete ---")
    print("Check the console output above to see the merge logic and final payload.")

if __name__ == "__main__":
    main()
