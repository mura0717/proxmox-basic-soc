#!/usr/bin/env python3
"""
Test creating a single asset via API with default valid values
"""

import os
import sys
import requests
import json
from typing import Dict, Optional
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.config import SNIPE_URL, HEADERS, VERIFY_SSL
from debug.asset_debug_logger import debug_logger

GRAPH_URL = "https://graph.microsoft.com/v1.0"
BEARER_TOKEN = "???" 

class GetAssetDetailsTest:
    """Microsoft Intune synchronization service"""
    
    def __init__(self, bearer_token: str):
        if not bearer_token:
            raise ValueError("Provide AZURE_BEARER_TOKEN env var with a valid Graph API token")
        self.bearer_token = bearer_token
            
    def get_asset_details(self, asset_id: str) -> Optional[Dict]:
        headers = {
            'Authorization': f'Bearer {self.bearer_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Get additional asset details
            url = f"{GRAPH_URL}/deviceManagement/managedDevices/{asset_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching asset details for {asset_id}: {e}")
            return None
    
if __name__ == "__main__":
    device_id = sys.argv[1]
    token = os.getenv("AZURE_BEARER_TOKEN")
    tester = GetAssetDetailsTest(token)
    details = tester.get_asset_details(device_id)
    if details:
        debug_logger.log_full_details(details, label=f"RAW INTUNE DEVICE {device_id}")
        print(f"Wrote details for {device_id} to {debug_logger.asset_all_details_log_file}")