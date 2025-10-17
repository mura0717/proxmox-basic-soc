#!/usr/bin/env python3
"""
Test creating a single asset via API with default valid values
"""

import os
import sys
import requests
import json
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.snipe_settings import SNIPE_URL, HEADERS, VERIFY_SSL

def get_valid_defaults():
    """Get first available model, status, and category IDs"""
    try:
        # Get first model
        model_resp = requests.get(f"{SNIPE_URL}/api/v1/models?limit=1", headers=HEADERS, verify=VERIFY_SSL)
        model_id = model_resp.json().get('rows', [{}])[0].get('id', 1) if model_resp.status_code == 200 else 1
        
        # Get first status
        status_resp = requests.get(f"{SNIPE_URL}/api/v1/statuslabels?limit=1", headers=HEADERS, verify=VERIFY_SSL)
        status_id = status_resp.json().get('rows', [{}])[0].get('id', 1) if status_resp.status_code == 200 else 1
        
        # Get first category
        category_resp = requests.get(f"{SNIPE_URL}/api/v1/categories?limit=1", headers=HEADERS, verify=VERIFY_SSL)
        category_id = category_resp.json().get('rows', [{}])[0].get('id', 1) if category_resp.status_code == 200 else 1
        
        return model_id, status_id, category_id
   
    except Exception as e:
        print(f"Error: {e}")
        return 1, 1, 1

def test_create_asset():
    print("Testing asset creation...")
    
    model_id, status_id, category_id = get_valid_defaults()
    print(f"Using - Model ID: {model_id}, Status ID: {status_id}, Category ID: {category_id}")
    
    test_asset = {
        "name": "Test-Asset-Debug",
        "asset_tag": f"TEST-{datetime.now().strftime('%H%M%S')}",
        "model_id": model_id, 
        "status_id": status_id,
        "category_id": category_id,  
        "notes": "Test asset for debugging"
    }
  
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
            result = response.json()
            if result.get('status') == 'success':
                print("✓ Asset created successfully!")
                print(f"Asset ID: {result.get('payload', {}).get('id')}")
            else:
                print("✗ Asset creation failed with errors:")
                print(result.get('messages', 'Unknown error'))
        else:
            print("✗ Asset creation failed")
            print(f"Response: {response.text}")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test_create_asset()