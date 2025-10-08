#!/usr/bin/env python3
"""
Debug script to check if Nmap-discovered assets are categorized correctly
Reads from parsed_asset_data.log (requires prior run with NMAP_DEBUG=1)
"""

import os
import sys
import json
import re
from typing import List, Dict
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.asset_categorizer import AssetCategorizer

class NmapDebugCategorization:
    """Test categorization logic for Nmap assets without needing live scans"""
    
    def __init__(self):
        self.debug = os.getenv('NMAP_CATEGORIZATION_DEBUG', '0') == '1'
        base_dir = os.path.dirname(os.path.abspath(__file__))
        self.log_dir = os.path.join(base_dir, "../logs/debug_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.nmap_log_categorized_assets = os.path.join(self.log_dir, "nmap_log_categorized_assets.log")
        self.parsed_log_path = os.path.join(self.log_dir, "parsed_asset_data.log")

    def get_nmap_assets(self) -> List[Dict]:
        """Extract Nmap assets from parsed_asset_data.log"""
        if not os.path.exists(self.parsed_log_path):
            print(f"ERROR: {self.parsed_log_path} not found!")
            print("Run this first: NMAP_DEBUG=1 python scanners/nmap_scanner.py [profile]")
            return []
        
        assets = []
        try:
            with open(self.parsed_log_path, 'r', encoding='utf-8') as file:
                content = file.read()
                
                # Split by the nmap section markers
                # Pattern: "--- PARSED ASSET DATA FROM NMAP ---"
                nmap_sections = re.split(r'--- PARSED ASSET DATA FROM NMAP ---', content)
                
                for section in nmap_sections[1:]:  # Skip first split (before first marker)
                    section = section.strip()
                    if not section:
                        continue
                    
                    # Extract the asset count line
                    lines = section.split('\n')
                    if not lines or not lines[0].startswith('Found'):
                        continue
                    
                    # Find JSON array boundaries
                    start = section.find('[')
                    end = section.rfind(']')
                    
                    if start == -1 or end == -1:
                        continue
                    
                    json_text = section[start:end+1].strip()
                    
                    try:
                        asset_list = json.loads(json_text)
                        # Filter for nmap assets (they have '_source': 'nmap')
                        nmap_assets = [a for a in asset_list if a.get('_source') == 'nmap']
                        assets.extend(nmap_assets)
                    except json.JSONDecodeError as e:
                        if self.debug:
                            print(f"JSON decode error: {e}")
                            print(f"Problematic text (first 100 chars): {json_text[:100]!r}")
                        continue
                        
        except Exception as e:
            print(f"Error reading {self.parsed_log_path}: {e}")
            return []
        
        return assets
    
    def write_nmap_assets_to_logfile(self):
        """Process and categorize Nmap assets from parsed log"""
        
        parsed_assets = self.get_nmap_assets()
        
        if not parsed_assets:
            print("No Nmap assets found in log. Ensure you've run:")
            print("  NMAP_DEBUG=1 python scanners/nmap_scanner.py [profile]")
            print("  Example: NMAP_DEBUG=1 python scanners/nmap_scanner.py discovery")
            return
        
        print(f"Loaded {len(parsed_assets)} parsed Nmap assets from log.")

        # Categorize each asset
        output_path = self.nmap_log_categorized_assets
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("# Nmap Categorization Test Results\n")
            f.write(f"# Generated: {datetime.now().isoformat()}\n")
            f.write(f"# Total assets: {len(parsed_assets)}\n\n")
            
            for i, asset in enumerate(parsed_assets, 1):
                # Asset is already parsed/transformed, just categorize
                categorization = AssetCategorizer.categorize(asset)
                
                output_data = {
                    "index": i,
                    "name": asset.get("name"),
                    "last_seen_ip": asset.get("last_seen_ip"),
                    "dns_hostname": asset.get("dns_hostname"),
                    "mac_address": asset.get("mac_addresses"),
                    "manufacturer": asset.get("manufacturer"),
                    "os_platform": asset.get("os_platform"),
                    "nmap_os_guess": asset.get("nmap_os_guess"),
                    "nmap_services": asset.get("nmap_services", []),
                    "scan_profile": asset.get("nmap_scan_profile"),
                    "device_type": categorization.get("device_type"),
                    "category": categorization.get("category"),
                    "cloud_provider": categorization.get("cloud_provider"),
                }
                
                f.write(json.dumps(output_data, indent=2))
                f.write("\n" + "-"*80 + "\n\n")
                
                # Print progress every 10 assets
                if i % 10 == 0:
                    print(f"Processed {i}/{len(parsed_assets)} assets...")
        
        print(f"\n✅ Wrote categorized results to: {output_path}")
        print(f"📊 Summary:")
        
        # Generate summary statistics
        category_stats = {}
        device_type_stats = {}
        
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
            # Count categories
            for line in content.split('\n'):
                if '"category":' in line:
                    category = line.split('"category": "')[1].split('"')[0]
                    category_stats[category] = category_stats.get(category, 0) + 1
                elif '"device_type":' in line:
                    device_type = line.split('"device_type": "')[1].split('"')[0]
                    device_type_stats[device_type] = device_type_stats.get(device_type, 0) + 1
        
        print("\nAssets by Category:")
        for category, count in sorted(category_stats.items(), key=lambda x: -x[1]):
            print(f"  {category:35} : {count}")
        
        print("\nAssets by Device Type:")
        for device_type, count in sorted(device_type_stats.items(), key=lambda x: -x[1]):
            print(f"  {device_type:35} : {count}")
        
        # Show scan profiles used
        scan_profiles = {}
        for asset in parsed_assets:
            profile = asset.get('nmap_scan_profile', 'unknown')
            scan_profiles[profile] = scan_profiles.get(profile, 0) + 1
        
        print("\nAssets by Scan Profile:")
        for profile, count in sorted(scan_profiles.items(), key=lambda x: -x[1]):
            print(f"  {profile:35} : {count}")

nmap_debug_categorization = NmapDebugCategorization()