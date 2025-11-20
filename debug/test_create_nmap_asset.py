"""
Test single Nmap discovered asset synchronization via Asset Matcher to Snipe-IT
for debugging purposes with regards to categorization and matching.
"""

import os
import sys
from pprint import pprint

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets_sync_library.asset_matcher import AssetMatcher

SAMPLE_PARSED_ASSET_DATA =   {
    "last_seen_ip": "192.168.1.67",
    "nmap_last_scan": "2025-11-20T14:54:14.896372+00:00",
    "nmap_scan_profile": "discovery",
    "name": "TL-SG108PE.Diabetes.local",
    "dns_hostname": "TL-SG108PE.Diabetes.local",
    "_source": "nmap",
    "mac_addresses": "3C:52:A1:68:FE:09",
    "nmap_open_ports": "80/tcp/http ( )",
    "open_ports_hash": "dedc83e356c7934001cf518f33b4e087",
    "nmap_services": [
      "http"
    ],
    "first_seen_date": "2025-11-20T14:54:14.896438+00:00"
}

def main():
    
    matcher = AssetMatcher()
    # Enable debug prints to see the logic flow
    matcher.debug = True
    
    print("=== Testing category determination ===")
    category = matcher._determine_category(SAMPLE_PARSED_ASSET_DATA)
    print("Determined Category Object:", category)
    
    print("\n=== Testing full asset payload preparation ===")
    print("\n[DEBUG] Simulating asset create process...")
    final_payload = matcher._prepare_asset_payload(SAMPLE_PARSED_ASSET_DATA)
    
    print("\nFinal payload that would be sent to Snipe-IT:")
    pprint(final_payload)

if __name__ == "__main__":
    main()