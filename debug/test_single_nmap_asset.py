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
    "last_seen_ip": "192.168.1.64",
    "nmap_last_scan": "2025-11-19T11:06:54.121507+00:00",
    "nmap_scan_profile": "discovery",
    "name": "AP7-Reception.Diabetes.local",
    "dns_hostname": "AP7-Reception.Diabetes.local",
    "_source": "nmap",
    "mac_addresses": "D0:21:F9:C7:97:E7",
    "manufacturer": "Ubiquiti Networks",
    "nmap_open_ports": "22/tcp/ssh ( )\n8080/tcp/http-proxy ( )",
    "open_ports_hash": "d374ef4e815def6c253e48ccae9a36dc",
    "nmap_services": [
      "ssh",
      "http-proxy"
    ],
    "first_seen_date": "2025-11-19T11:06:54.121518+00:00"
}

def main():
    
    matcher = AssetMatcher()
    # Enable debug prints to see the logic flow
    matcher.debug = True
    
    print("=== Testing category determination ===")
    category = matcher._determine_category(SAMPLE_PARSED_ASSET_DATA)
    print("Determined Category Object:", category)
    
    print("\n=== Testing full asset payload preparation ===")
    # We call the main preparation method to simulate the real workflow
    final_payload = matcher._prepare_asset_payload(SAMPLE_PARSED_ASSET_DATA)
    
    print("\nFinal payload that would be sent to Snipe-IT:")
    pprint(final_payload)

if __name__ == "__main__":
    main()