"""
Test single Nmap discovered asset synchronization via Asset Matcher to Snipe-IT
for debugging purposes with regards to categorization and matching.
"""

import os
import sys
from pprint import pprint


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets_sync_library.asset_matcher import AssetMatcher

SAMPLE_ASSET = {
    "model_id": 1,
    "category_id": 19,
    "name": "AP2-ITkontor.Diabetes.local",
    "asset_tag": "AUTO-20251117150303-CB8C49",
    "mac_address": "D0:21:F9:C7:6F:D7",
    "status_id": 18,
    "_snipeit_model_50": "Generic Unknown Device",
    "_snipeit_manufacturer_51": "Ubiquiti Networks",
    "_snipeit_dns_hostname_62": "AP2-ITkontor.Diabetes.local",
    "_snipeit_mac_addresses_63": "D0:21:F9:C7:6F:D7",
    "_snipeit_last_seen_ip_64": "192.168.1.62",
    "_snipeit_first_seen_date_96": "2025-11-17T14:15:26.786470+00:00",
    "_snipeit_nmap_last_scan_97": "2025-11-17T14:15:26.786391+00:00",
    "_snipeit_nmap_open_ports_100": "22/tcp/ssh ( )\n8080/tcp/http-proxy ( )",
    "_snipeit_open_ports_hash_101": "d374ef4e815def6c253e48ccae9a36dc",
    "_snipeit_last_update_source_105": "nmap",
    "_snipeit_last_update_at_106": "2025-11-17T14:15:51.001398+00:00"
}

def main():
    
    matcher = AssetMatcher()
    
    print("=== Testing category determination ===")
    category = matcher._determine_category(SAMPLE_ASSET)
    print("Category result:", category)
    
    print("\n=== Testing full model/manufacturer/category assignment ===")
    payload = {}
    result_payload = matcher._assign_model_manufacturer_category(payload, SAMPLE_ASSET)
    
    print("\nFinal payload that would be sent to Snipe-IT:")
    pprint(result_payload)

if __name__ == "__main__":
    main()