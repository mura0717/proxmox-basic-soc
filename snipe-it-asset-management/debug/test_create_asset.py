#!/usr/bin/env python3
"""
Test creating a single asset via API
"""

import os
import sys
import requests
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.config import SNIPE_URL, HEADERS, VERIFY_SSL

def test_create_asset():
    # Simple test asset
    test_asset = {
        "name": "Test-Asset-Debug",
        "asset_tag": "TEST-DEBUG-001",
        "model_id": 1, 
        "status_id": 1,  
        "notes": "Test asset for debugging"
    }
    
    print("Testing asset creation...")
    print(f"Payload: {json.dumps(test_asset, indent=2)}")
    
    try:
        response = requests.post(
            f"{SNIPE_URL}/api/v1/hardware",
            headers=HEADERS,
            json=test_asset,
            verify=VERIFY_SSL
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✓ Asset created successfully!")
            asset_data = response.json()
            print(f"Asset ID: {asset_data.get('id')}")
        else:
            print("✗ Asset creation failed")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_create_asset()