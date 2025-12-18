"""
Test single Nmap discovered asset synchronization via Asset Matcher to Snipe-IT
for debugging purposes with regards to categorization and matching.
"""

from pprint import pprint

from proxmox_soc.asset_engine.asset_matcher import AssetMatcher

SAMPLE_PARSED_ASSET_DATA =   {
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