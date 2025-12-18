#!/usr/bin/env python3

print("Testing module imports...")

try:
    from proxmox_soc.config.settings import SNIPE
    print("✓ Config import works")
except Exception as e:
    print(f"✗ Config import failed: {e}")

try:
    from proxmox_soc.snipe_it.snipe_api.snipe_client import make_api_request
    print("✓ API client import works")
except Exception as e:
    print(f"✗ API client import failed: {e}")

try:
    from proxmox_soc.snipe_it.snipe_api.services.crudbase import BaseCRUDService
    print("✓ CRUD base import works")
except Exception as e:
    print(f"✗ CRUD base import failed: {e}")

try:
    from proxmox_soc.asset_engine.asset_matcher import AssetMatcher
    print("✓ Asset matcher import works")
except Exception as e:
    print(f"✗ Asset matcher import failed: {e}")

try:
    from proxmox_soc.scanners.nmap_scanner import NmapScanner
    print("✓ Nmap scanner import works")
except Exception as e:
    print(f"✗ Nmap scanner import failed: {e}")

print("\nAll imports successful! You can now run:")
print("  python3 scanners/nmap_scanner.py discovery")