#!/usr/bin/env python3
"""
Debug script to check Snipe-IT assets and API responses
Verifies Snipe-IT API connectivity, lists recent assets and inspects custom-field setup; 
Useful for quick troubleshooting of the Snipe-IT integration.
"""

import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.config import SNIPE_URL, HEADERS, VERIFY_SSL

def snipeit_api_debug():
    print("=== Snipe-IT Asset Debug ===")
    
    # Test API connection
    print("1. Testing API connection...")
    try:
        response = requests.get(f"{SNIPE_URL}/api/v1/statuslabels", 
                              headers=HEADERS, verify=VERIFY_SSL)
        if response.status_code == 200:
            print("✓ API connection successful")
        else:
            print(f"✗ API connection failed: {response.status_code}")
            return
    except Exception as e:
        print(f"✗ API connection error: {e}")
        return
    
    # Check total assets
    print("\n2. Checking total assets...")
    try:
        response = requests.get(f"{SNIPE_URL}/api/v1/hardware?limit=1", 
                              headers=HEADERS, verify=VERIFY_SSL)
        if response.status_code == 200:
            data = response.json()
            total = data.get('total', 0)
            print(f"Total assets in system: {total}")
        else:
            print(f"Failed to get asset count: {response.status_code}")
    except Exception as e:
        print(f"Error getting asset count: {e}")
    
    # Get all assets with details
    print("\n3. Checking recent assets...")
    try:
        response = requests.get(f"{SNIPE_URL}/api/v1/hardware?limit=100&sort=created_at&order=desc", 
                              headers=HEADERS, verify=VERIFY_SSL)
        if response.status_code == 200:
            data = response.json()
            assets = data.get('rows', [])
            print(f"Found {len(assets)} assets in API response")
            
            if assets:
                print("\nRecent assets:")
                for i, asset in enumerate(assets[:10]):  # Show first 10
                    print(f"  {i+1}. {asset.get('name', 'Unknown')} - {asset.get('asset_tag', 'No tag')} - ID: {asset.get('id')}")
            else:
                print("No assets found in API response")
                
        else:
            print(f"Failed to get assets: {response.status_code}")
    except Exception as e:
        print(f"Error getting assets: {e}")
    
    # Check custom fields setup
    print("\n4. Checking custom fields...")
    try:
        response = requests.get(f"{SNIPE_URL}/api/v1/fields", 
                              headers=HEADERS, verify=VERIFY_SSL)
        if response.status_code == 200:
            data = response.json()
            fields = data.get('rows', [])
            print(f"Custom fields configured: {len(fields)}")
        else:
            print(f"Failed to get custom fields: {response.status_code}")
    except Exception as e:
        print(f"Error checking custom fields: {e}")

if __name__ == "__main__":
    snipeit_api_debug()