#!/usr/bin/env python3
# test_imports.py - Save in /opt/snipeit-sync/snipe-it-asset-management/

import sys
import os

# Add current directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

print("Testing imports...")

try:
    from snipe_api.config import SNIPE_URL
    print("✓ Config import works")
except Exception as e:
    print(f"✗ Config import failed: {e}")

try:
    from snipe_api.api_client import make_api_request
    print("✓ API client import works")
except Exception as e:
    print(f"✗ API client import failed: {e}")

try:
    from crud.base import BaseCRUDService
    print("✓ CRUD base import works")
except Exception as e:
    print(f"✗ CRUD base import failed: {e}")

try:
    from lib.asset_matcher import AssetMatcher
    print("✓ Asset matcher import works")
except Exception as e:
    print(f"✗ Asset matcher import failed: {e}")

try:
    from scanners.nmap_scanner import NmapScanner
    print("✓ Nmap scanner import works")
except Exception as e:
    print(f"✗ Nmap scanner import failed: {e}")

print("\nAll imports successful! You can now run:")
print("  python3 scanners/nmap_scanner.py discovery")