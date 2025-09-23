#!/usr/bin/env python3
# check_assets.py

import sys
sys.path.insert(0, '/opt/snipeit-sync/snipe-it-asset-management')

from crud.base import BaseCRUDService

# Check all endpoints
endpoints = [
    ('/api/v1/hardware', 'Assets'),
    ('/api/v1/models', 'Models'),
    ('/api/v1/manufacturers', 'Manufacturers'),
    ('/api/v1/statuslabels', 'Status Labels'),
    ('/api/v1/categories', 'Categories')
]

for endpoint, name in endpoints:
    service = BaseCRUDService(endpoint, name)
    items = service.get_all()
    print(f"{name}: {len(items)} items")
    
    # Show first few items
    for item in items[:3]:
        print(f"  - {item.get('name', 'unnamed')} (ID: {item.get('id')})")