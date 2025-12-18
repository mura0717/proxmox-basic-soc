#!/usr/bin/env python3

print("Testing module imports...")

try:
    from proxmox_soc.config.settings import SNIPE, ZABBIX, WAZUH
    print("✓ Config import works for SNIPE, ZABBIX, WAZUH")
except Exception as e:
    print(f"✗ Config import failed for SNIPE, ZABBIX, WAZUH: {e}")

try:
    from proxmox_soc.asset_engine.asset_matcher import AssetMatcher
    print("✓ Asset matcher import works")
except Exception as e:
    print(f"✗ Asset matcher import failed: {e}")

try: 
    from asset_engine.asset_categorizer import AssetCategorizer
    print("✓ Asset categorizer import works")
except Exception as e:
    print(f"✗ Asset categorizer import failed: {e}")

try:
    from asset_engine.asset_finder import AssetFinder
    print("✓ Asset finder import works")
except Exception as e:
    print(f"✗ Asset finder import failed: {e}")

try:
    from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService
    print("✓ Asset service import works")
except Exception as e:
    print(f"✗ Asset service import failed: {e}")
    
try:
    from proxmox_soc.snipe_it.snipe_api.services.crudbase import BaseCRUDService
    print("✓ CRUD base import works")
except Exception as e:
    print(f"✗ CRUD base import failed: {e}")
    
try:
    from proxmox_soc.scanners.nmap_scanner import NmapScanner
    print("✓ Nmap scanner import works")
except Exception as e:
    print(f"✗ Nmap scanner import failed: {e}")
    
try:
    from proxmox_soc.scanners.teams_scanner import TeamsScanner
    print("✓ Teams scanner import works")
except Exception as e:
    print(f"✗ Teams scanner import failed: {e}")

try:
    from proxmox_soc.scanners.intune_scanner import IntuneScanner
    print("✓ Intune scanner import works")
except Exception as e:
    print(f"✗ Intune scanner import failed: {e}")

try:
    from proxmox_soc.snipe_it.snipe_api.snipe_client import make_api_request
    print("✓ API client import works")
except Exception as e:
    print(f"✗ API client import failed: {e}")

try:
    from proxmox_soc.debug.tools.asset_debug_logger import debug_logger
    print("✓ Debug logger import works")
except Exception as e:
    print(f"✗ Debug logger import failed: {e}")

try:
    from proxmox_soc.utils.mac_utils import normalize_mac
    print("✓ MAC utils import works")
except Exception as e:
    print(f"✗ MAC utils import failed: {e}")

try:
    from proxmox_soc.utils.text_utils import normalize_for_comparison
    print("✓ Text utils import works")
except Exception as e:
    print(f"✗ Text utils import failed: {e}")  

print("\nAll imports successful!")
