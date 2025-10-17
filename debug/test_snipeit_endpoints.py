#!/usr/bin/env python3
"""
Debug script to API responses
"""

import os
import sys
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.snipe_settings import SNIPE_URL, HEADERS, VERIFY_SSL

endpoints = [
    ('/api/v1/hardware', 'Assets'),
    ('/api/v1/models', 'Models'),
    ('/api/v1/manufacturers', 'Manufacturers'),
    ('/api/v1/statuslabels', 'Status Labels'),
    ('/api/v1/categories', 'Categories'),
    ('/api/v1/locations', 'Locations'),
    ('/api/v1/users', 'Users'),
    ('/api/v1/licenses', 'Licenses'),
    ('/api/v1/fields', 'Fields'),
    ('/api/v1/fieldsets', 'Fieldsets'),
    ('/api/v1/companies', 'Companies'),
    ('/api/v1/accessories', 'Accessories'),
    ('/api/v1/components', 'Components'),
    ('/api/v1/consumables', 'Consumables'),
    ('/api/v1/suppliers', 'Suppliers'),
    ('/api/v1/groups', 'Groups'),
    ('/api/v1/departments', 'Departments'),
    ('/api/v1/reports/activity', 'Reports'),
    ('/api/v1/version', 'Misc'),
    ('/api/v1/settings/backups', 'Settings')
]

positive_results = []
negative_results = []

def check_endpoints():
    print("=== Snipe-IT Endpoint Check ===")
    
    # Test API connection
    print("1. Testing API connections...")
    for endpoint, name in endpoints:
        print(f"Checking {name} endpoint...")    
        try:
            response = requests.get(f"{SNIPE_URL}{endpoint}", headers=HEADERS, verify=VERIFY_SSL)
            if response.status_code == 200:
                positive_results.append((name, "✓ ", response.status_code))
            else:
                negative_results.append((name, f"✗ ", response.status_code))
                return
        except Exception as e:
            print(f"✗ API connection test error: {e}")
            return

check_endpoints()
print("Successful Endpoints: ", positive_results)
print("Failed Endpoints: ", negative_results)