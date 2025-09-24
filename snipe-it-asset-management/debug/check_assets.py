#!/usr/bin/env python3
# check_assets.py

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crud.base import BaseCRUDService

endpoints = [
    ('/api/v1/hardware', 'Assets'),
    ('/api/v1/models', 'Models'),
    ('/api/v1/manufacturers', 'Manufacturers'),
    ('/api/v1/statuslabels', 'Status Labels'),
    ('/api/v1/categories', 'Categories'),
]

for endpoint, name in endpoints:
    service = BaseCRUDService(endpoint, name)
    items = service.get_all()
    print(f"{name}: {len(items)} items")
    
    # Show first few items
    for item in items[:3]:
        print(f"  - {item.get('name', 'unnamed')} (ID: {item.get('id')})")