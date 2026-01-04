#!/usr/bin/env python3

"""
Hydra Pipeline Integration Test
Tests the full flow: Scanner -> Matcher -> Builder -> Dispatcher (dry-run)
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Setup path to allow imports
BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR))
ENV_PATH = BASE_DIR / '.env'

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

from proxmox_soc.asset_engine.asset_matcher import AssetMatcher
from proxmox_soc.builders.snipe_builder import SnipePayloadBuilder
from proxmox_soc.builders.zabbix_builder import ZabbixPayloadBuilder
from proxmox_soc.builders.wazuh_builder import WazuhPayloadBuilder

INTEGRATION_TESTS = os.getenv("HYDRA_INTEGRATION_TESTS", "0") == "1"
SNIPE_AVAILABLE = bool(os.getenv("SNIPE_API_TOKEN"))

def print_result(test_name: str, passed: bool, details: str = ""):
    symbol = "✓" if passed else "✗"
    color = "\033[92m" if passed else "\033[91m"
    reset = "\033[0m"
    print(f"[{color}{symbol}{reset}] {test_name}")
    if details:
        print(f"    {details}")

def get_mock_nmap_assets() -> List[Dict]:
    """Generate mock Nmap scan data"""
    return [
        {
            "last_seen_ip": "192.168.1.100",
            "name": "test-server-01",
            "dns_hostname": "test-server-01.local",
            "mac_addresses": "AA:BB:CC:DD:EE:FF",
            "manufacturer": "Dell Inc.",
            "model": "PowerEdge R640",
            "nmap_services": ["ssh", "http", "https"],
            "nmap_open_ports": "22/tcp/ssh\n80/tcp/http\n443/tcp/https",
            "_source": "nmap"
        },
        {
            "last_seen_ip": "192.168.1.101",
            "name": "Device-192.168.1.101",  # Generic name - should be skippable
            "dns_hostname": "",
            "_source": "nmap"
        }
    ]

def get_mock_ms365_assets() -> List[Dict]:
    """Generate mock MS365 data"""
    return [
        {
            "name": "LAPTOP-USER01",
            "serial": "ABC123XYZ",
            "manufacturer": "Lenovo",
            "model": "ThinkPad X1 Carbon",
            "os_platform": "Windows",
            "os_version": "11",
            "intune_device_id": "intune-device-001",
            "azure_ad_id": "azure-ad-001",
            "primary_user_upn": "user@company.com",
            "mac_addresses": "11:22:33:44:55:66",
            "_source": "microsoft365"
        }
    ]

def test_matcher():
    """Test AssetMatcher with mock data"""
    print("\n=== Testing AssetMatcher ===")
    
    try:
        matcher = AssetMatcher()
        
        # Test with Nmap data
        nmap_assets = get_mock_nmap_assets()
        actions = matcher.process_scan_data("nmap", nmap_assets)
        
        print_result(
            "Matcher processes Nmap data",
            len(actions) >= 1,
            f"Generated {len(actions)} actions from {len(nmap_assets)} assets"
        )
        
        # Verify action structure
        if actions:
            action = actions[0]
            has_required = all(k in action for k in ['action', 'snipe_id', 'canonical_data'])
            print_result(
                "Action object has correct structure",
                has_required,
                f"Keys: {list(action.keys())}"
            )
        
        # Test with MS365 data
        ms365_assets = get_mock_ms365_assets()
        actions_ms365 = matcher.process_scan_data("microsoft365", ms365_assets)
        
        print_result(
            "Matcher processes MS365 data",
            len(actions_ms365) >= 1,
            f"Generated {len(actions_ms365)} actions"
        )
        
        return True
        
    except Exception as e:
        print_result("AssetMatcher", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_snipe_builder():
    """Test SnipePayloadBuilder"""
    print("\n=== Testing SnipePayloadBuilder ===")
    
    try:
        builder = SnipePayloadBuilder()
        
        # Mock action object
        action = {
            "action": "create",
            "snipe_id": None,
            "canonical_data": {
                "name": "Test-Device",
                "serial": "TEST123",
                "manufacturer": "Dell",
                "model": "OptiPlex 7090",
                "mac_addresses": "AA:BB:CC:DD:EE:FF",
                "_source": "nmap"
            }
        }
        
        payload = builder.build(action)
        
        # Check required fields
        has_name = 'name' in payload
        has_model_id = 'model_id' in payload
        has_status_id = 'status_id' in payload
        
        print_result(
            "Builder generates valid payload",
            has_name and has_model_id,
            f"Payload keys: {list(payload.keys())[:8]}..."
        )
        
        print_result(
            "Payload has name",
            payload.get('name') == "Test-Device"
        )
        
        print_result(
            "Payload has asset_tag (auto-generated)",
            'asset_tag' in payload and payload['asset_tag'].startswith('AUTO-')
        )
        
        return True
        
    except Exception as e:
        print_result("SnipePayloadBuilder", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_zabbix_builder():
    """Test ZabbixPayloadBuilder"""
    print("\n=== Testing ZabbixPayloadBuilder ===")
    
    try:
        builder = ZabbixPayloadBuilder()
        
        action = {
            "action": "create",
            "snipe_id": 123,
            "canonical_data": {
                "name": "Test-Server",
                "last_seen_ip": "192.168.1.100",
                "device_type": "Server",
                "serial": "SRV001",
                "_source": "nmap"
            },
            "snipe_payload": {"name": "Test-Server"}
        }
        
        group_name = builder.get_group_name("Server")
        print_result(
            "Group name mapping works",
            group_name == "Servers",
            f"'Server' -> '{group_name}'"
        )
        
        payload = builder.build_host(action, "1")
        
        print_result(
            "Zabbix host payload has required fields",
            all(k in payload for k in ['host', 'name', 'groups', 'interfaces']),
            f"Keys: {list(payload.keys())}"
        )
        
        print_result(
            "Interface has IP",
            payload['interfaces'][0]['ip'] == "192.168.1.100"
        )
        
        return True
        
    except Exception as e:
        print_result("ZabbixPayloadBuilder", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_wazuh_builder():
    """Test WazuhPayloadBuilder"""
    print("\n=== Testing WazuhPayloadBuilder ===")
    
    try:
        builder = WazuhPayloadBuilder()
        
        action = {
            "action": "create",
            "snipe_id": 456,
            "canonical_data": {
                "name": "Test-Device",
                "last_seen_ip": "192.168.1.50",
                "nmap_open_ports": "22/tcp/ssh\n80/tcp/http",
                "device_type": "Desktop",
                "_source": "nmap"
            },
            "snipe_payload": {"name": "Test-Device", "asset_tag": "AUTO-123"}
        }
        
        event = builder.build_event(action)
        
        print_result(
            "Event has required structure",
            all(k in event for k in ['timestamp', 'event_type', 'action', 'asset', 'security']),
            f"Keys: {list(event.keys())}"
        )
        
        print_result(
            "Open ports parsed correctly",
            len(event['security']['open_ports']) == 2,
            f"Ports: {event['security']['open_ports']}"
        )
        
        print_result(
            "VLAN detection works",
            event['security']['vlan'] is not None,
            f"VLAN: {event['security']['vlan']}"
        )
        
        return True
        
    except Exception as e:
        print_result("WazuhPayloadBuilder", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_full_pipeline():
    """Test complete pipeline with mock data"""
    print("\n=== Testing Full Pipeline (Dry Run) ===")
    
    try:
        from proxmox_soc.asset_engine.asset_matcher import AssetMatcher
        from proxmox_soc.builders.snipe_builder import SnipePayloadBuilder
        
        # 1. Matcher
        matcher = AssetMatcher()
        assets = get_mock_nmap_assets()
        actions = matcher.process_scan_data("nmap", assets)
        
        # 2. Builder
        builder = SnipePayloadBuilder()
        for action in actions:
            action['snipe_payload'] = builder.build(action)
        
        # 3. Verify final structure
        valid_actions = sum(1 for a in actions 
                          if 'snipe_payload' in a and 'canonical_data' in a)
        
        print_result(
            "Pipeline produces valid action objects",
            valid_actions == len(actions),
            f"{valid_actions}/{len(actions)} actions have complete data"
        )
        
        # Show sample output
        if actions:
            sample = actions[0]
            print("\n  Sample action object:")
            print(f"    action: {sample['action']}")
            print(f"    snipe_id: {sample['snipe_id']}")
            print(f"    canonical_data.name: {sample['canonical_data'].get('name')}")
            print(f"    snipe_payload.name: {sample['snipe_payload'].get('name')}")
            print(f"    snipe_payload.model_id: {sample['snipe_payload'].get('model_id')}")
        
        return True
        
    except Exception as e:
        print_result("Full Pipeline", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("HYDRA PIPELINE INTEGRATION TEST")
    print("Mode: DRY RUN (No Assets will be created/modified)")
    print("=" * 60)
    
    results = []
    
    results.append(("Zabbix Builder", test_zabbix_builder()))
    results.append(("Wazuh Builder", test_wazuh_builder()))
    
    if INTEGRATION_TESTS and SNIPE_AVAILABLE:
        results.append(("Matcher", test_matcher()))
        results.append(("Snipe Builder", test_snipe_builder()))
        results.append(("Full Pipeline", test_full_pipeline()))
    else:
        print("\n[SKIP] Snipe-IT integration tests")
        if not SNIPE_AVAILABLE:
            print("       Reason: SNIPE_API_TOKEN is missing in .env")
        elif not INTEGRATION_TESTS:
            print("       Reason: HYDRA_INTEGRATION_TESTS environment variable is not set to '1'")
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, r in results if r)
    total = len(results)
    
    for name, result in results:
        symbol = "✓" if result else "✗"
        color = "\033[92m" if result else "\033[91m"
        reset = "\033[0m"
        print(f"  [{color}{symbol}{reset}] {name}")
    
    print(f"\nTotal: {passed}/{total} passed")
    return 0 if passed == total else 1

if __name__ == "__main__":
    sys.exit(main())