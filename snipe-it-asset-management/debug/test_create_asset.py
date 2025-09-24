#!/usr/bin/env python3
"""
Test creating a single asset via API with default valid values
"""

import os
import sys
import requests
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.config import SNIPE_URL, HEADERS, VERIFY_SSL

def test_create_asset():
    
    print("Testing asset creation...")
    print(f"Payload: {json.dumps(test_asset, indent=2)}")
    
    def get_valid_defaults():
        """Get valid default model, status, and category IDs"""
        try:
            model_resp = requests.get(f"{SNIPE_URL}/api/v1/models", headers=HEADERS, verify=VERIFY_SSL)
            status_resp = requests.get(f"{SNIPE_URL}/api/v1/statuslabels", headers=HEADERS, verify=VERIFY_SSL)
            category_resp = requests.get(f"{SNIPE_URL}/api/v1/categories", headers=HEADERS, verify=VERIFY_SSL)
            
            model_id = model_resp.json().get('rows', [{}])[0].get('id', 1) if model_resp.status_code == 200 else 1
            status_id = status_resp.json().get('rows', [{}])[0].get('id', 1) if status_resp.status_code == 200 else 1
            category_id = category_resp.json().get('rows', [{}])[0].get('id', 1) if category_resp.status_code == 200 else 1
            return model_id, status_id, category_id
        except Exception as e:
            print(f"Error fetching defaults: {e}")
            return 1, 1, 1
    
    model_id, status_id, category_id = get_valid_defaults()
    
    test_asset = {
        "name": "Test-Asset-Debug",
        "asset_tag": "TEST-DEBUG-001",
        "model_id": model_id, 
        "status_id": status_id,
        "category_id": category_id,  
        "notes": "Test asset for debugging"
    }
        
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