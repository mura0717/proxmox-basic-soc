#!/usr/bin/env python3
"""
Hydra Pipeline Integration Test
Tests the full flow: Scanner -> Resolver -> State -> Builder -> Dispatcher (dry-run)
"""

import os
import sys
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv

# Setup path
BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.append(str(BASE_DIR))
ENV_PATH = BASE_DIR / '.env'

if ENV_PATH.exists():
    load_dotenv(ENV_PATH)
else:
    load_dotenv()

# Import refactored components
from proxmox_soc.asset_engine.asset_resolver import AssetResolver, ResolvedAsset
from proxmox_soc.states.snipe_state import SnipeStateManager
from proxmox_soc.states.wazuh_state import WazuhStateManager
from proxmox_soc.states.zabbix_state import ZabbixStateManager
from proxmox_soc.builders.snipe_builder import SnipePayloadBuilder
from proxmox_soc.builders.zabbix_builder import ZabbixPayloadBuilder
from proxmox_soc.builders.wazuh_builder import WazuhPayloadBuilder
from proxmox_soc.states.base_state import StateResult

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
        },
        {
            "last_seen_ip": "192.168.1.101",
            "name": "Device-192.168.1.101",
            "dns_hostname": "",
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
        }
    ]


def test_resolver():
    """Test AssetResolver"""
    print("\n=== Testing AssetResolver ===")
    
    try:
        resolver = AssetResolver()
        
        # Test with Nmap data
        nmap_assets = get_mock_nmap_assets()
        resolved = resolver.resolve("nmap", nmap_assets)
        
        print_result(
            "Resolver returns ResolvedAsset objects",
            all(isinstance(r, ResolvedAsset) for r in resolved),
            f"Got {len(resolved)} ResolvedAsset objects"
        )
        
        print_result(
            "Source is tagged correctly",
            all(r.canonical_data.get('_source') == 'nmap' for r in resolved),
            f"All assets tagged with 'nmap'"
        )
        
        return True
        
    except Exception as e:
        print_result("AssetResolver", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_snipe_state():
    """Test SnipeStateManager"""
    print("\n=== Testing SnipeStateManager ===")
    
    if not SNIPE_AVAILABLE:
        print("  [SKIP] Snipe-IT not configured")
        return True
    
    try:
        state = SnipeStateManager()
        
        # Test with asset that has serial
        asset_with_serial = {"serial": "TEST123", "name": "Test Device"}
        result = state.check(asset_with_serial)
        
        print_result(
            "State check returns StateResult",
            isinstance(result, StateResult),
            f"Action: {result.action}"
        )
        
        print_result(
            "Generate ID works",
            state.generate_id(asset_with_serial) is not None,
            f"ID: {state.generate_id(asset_with_serial)}"
        )
        
        return True
        
    except Exception as e:
        print_result("SnipeStateManager", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wazuh_state():
    """Test WazuhStateManager"""
    print("\n=== Testing WazuhStateManager ===")
    
    try:
        from tempfile import TemporaryDirectory
        
        with TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "wazuh_state.json"
            state = WazuhStateManager(state_file)
            
            # Test new asset
            asset = {"serial": "WAZUH001", "name": "Test Device", "last_seen_ip": "192.168.1.50"}
            result = state.check(asset)
            
            print_result(
                "New asset returns 'create'",
                result.action == 'create',
                f"Action: {result.action}"
            )
            
            # Record and check again
            state.record(result.asset_id, asset, 'create')
            result2 = state.check(asset)
            
            print_result(
                "Unchanged asset returns 'skip'",
                result2.action == 'skip',
                f"Action: {result2.action}"
            )
            
            # Modify and check
            asset['last_seen_ip'] = "192.168.1.60"
            result3 = state.check(asset)
            
            print_result(
                "Changed asset returns 'update'",
                result3.action == 'update',
                f"Action: {result3.action}"
            )
            
        return True
        
    except Exception as e:
        print_result("WazuhStateManager", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_zabbix_state():
    """Test ZabbixStateManager"""
    print("\n=== Testing ZabbixStateManager ===")
    
    try:
        state = ZabbixStateManager()
        
        # Test monitorable asset (needs IP)
        asset = {
            "name": "Test-Zabbix-Host",
            "last_seen_ip": "192.168.1.200",
            "mac_addresses": "11:22:33:44:55:66",
            "device_type": "Server"
        }
        
        result = state.check(asset)
        
        print_result(
            "State check returns StateResult",
            isinstance(result, StateResult),
            f"Action: {result.action}"
        )
        
        print_result(
            "Generate ID works (MAC priority)",
            result.asset_id == "zabbix:mac:11:22:33:44:55:66",
            f"ID: {result.asset_id}"
        )
        
        return True
        
    except Exception as e:
        print_result("ZabbixStateManager", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_snipe_builder():
    """Test SnipePayloadBuilder"""
    print("\n=== Testing SnipePayloadBuilder ===")
    
    if not SNIPE_AVAILABLE:
        print("  [SKIP] Snipe-IT not configured")
        return True
    
    try:
        builder = SnipePayloadBuilder()
        
        asset_data = {
            "name": "Test-Device",
            "serial": "TEST123",
            "manufacturer": "Dell",
            "model": "OptiPlex 7090",
            "mac_addresses": "AA:BB:CC:DD:EE:FF",
            "_source": "nmap"
        }
        
        state_result = StateResult(
            action='create',
            asset_id='snipe:serial:TEST123',
            existing=None,
            reason='New asset'
        )
        
        build_result = builder.build(asset_data, state_result)
        
        print_result(
            "Builder returns BuildResult",
            hasattr(build_result, 'payload'),
            f"Keys: {list(build_result.payload.keys())[:5]}..."
        )
        
        print_result(
            "Payload has required fields",
            all(k in build_result.payload for k in ['name', 'model_id']),
            f"Has name and model_id"
        )
        
        print_result(
            "Auto-generated asset_tag",
            build_result.payload.get('asset_tag', '').startswith('AUTO-'),
            f"Tag: {build_result.payload.get('asset_tag')}"
        )
        
        return True
        
    except Exception as e:
        print_result("SnipePayloadBuilder", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_wazuh_builder():
    """Test WazuhPayloadBuilder"""
    print("\n=== Testing WazuhPayloadBuilder ===")
    
    try:
        builder = WazuhPayloadBuilder()
        
        asset_data = {
            "name": "Test-Device",
            "last_seen_ip": "192.168.1.50",
            "nmap_open_ports": "22/tcp/ssh\n80/tcp/http",
            "device_type": "Desktop",
            "_source": "nmap"
        }
        
        state_result = StateResult(
            action='create',
            asset_id='serial:TEST123',
            existing=None,
            reason='New asset'
        )
        
        build_result = builder.build(asset_data, state_result)
        event = build_result.payload
        
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
            event['security']['vlan'] == "Primary LAN",
            f"VLAN: {event['security']['vlan']}"
        )
        
        return True
        
    except Exception as e:
        print_result("WazuhPayloadBuilder", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_zabbix_builder():
    """Test ZabbixPayloadBuilder"""
    print("\n=== Testing ZabbixPayloadBuilder ===")
    
    try:
        builder = ZabbixPayloadBuilder()
        
        asset_data = {
            "name": "Test-Server",
            "last_seen_ip": "192.168.1.100",
            "device_type": "Server",
            "serial": "SRV001",
            "_source": "nmap"
        }
        
        state_result = StateResult(
            action='create',
            asset_id='mac:112233445566',
            existing=None,
            reason='New host'
        )
        
        build_result = builder.build(asset_data, state_result)
        payload = build_result.payload
        
        print_result(
            "Group name mapping works",
            build_result.metadata.get('group_name') == "Servers",
            f"Group: {build_result.metadata.get('group_name')}"
        )
        
        print_result(
            "Payload has required fields",
            all(k in payload for k in ['host', 'name', 'groups', 'interfaces']),
            f"Keys: {list(payload.keys())}"
        )
        
        print_result(
            "Interface has correct IP",
            payload['interfaces'][0]['ip'] == "192.168.1.100",
            f"IP: {payload['interfaces'][0]['ip']}"
        )
        
        return True
        
    except Exception as e:
        print_result("ZabbixPayloadBuilder", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_full_pipeline():
    """Test complete pipeline with mock data"""
    print("\n=== Testing Full Pipeline (Dry Run) ===")
    
    if not SNIPE_AVAILABLE:
        print("  [SKIP] Snipe-IT not configured")
        return True
    
    try:
        from proxmox_soc.pipelines.integration_pipeline import IntegrationPipeline
        from tempfile import TemporaryDirectory
        
        resolver = AssetResolver()
        assets = get_mock_nmap_assets()
        resolved = resolver.resolve("nmap", assets)
        
        # Test Wazuh pipeline (file-based, always works)
        with TemporaryDirectory() as tmpdir:
            state_file = Path(tmpdir) / "wazuh_state.json"
            
            pipeline = IntegrationPipeline(
                name='Wazuh-Test',
                state=WazuhStateManager(state_file),
                builder=WazuhPayloadBuilder(),
                dispatcher=None,  # We'll test with dry_run
                dry_run=True
            )
            
            # Replace dispatcher.sync to avoid None error
            pipeline.dispatcher = type('MockDispatcher', (), {'sync': lambda self, x: {'created': len(x), 'updated': 0, 'failed': 0}})()
            
            result = pipeline.process(resolved)
            
            print_result(
                "Pipeline processes assets",
                result.created + result.skipped > 0,
                f"Created: {result.created}, Skipped: {result.skipped}"
            )
        
        return True
        
    except Exception as e:
        print_result("Full Pipeline", False, f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    print("=" * 60)
    print("HYDRA PIPELINE INTEGRATION TEST")
    print("Mode: DRY RUN (No changes will be made)")
    print("=" * 60)
    
    results = []
    
    # Core tests (always run)
    results.append(("Resolver", test_resolver()))
    results.append(("Wazuh State", test_wazuh_state()))
    results.append(("Zabbix State", test_zabbix_state()))
    results.append(("Wazuh Builder", test_wazuh_builder()))
    results.append(("Zabbix Builder", test_zabbix_builder()))
    
    # Integration tests (require config)
    if INTEGRATION_TESTS and SNIPE_AVAILABLE:
        results.append(("Snipe State", test_snipe_state()))
        results.append(("Snipe Builder", test_snipe_builder()))
        results.append(("Full Pipeline", test_full_pipeline()))
    else:
        print("\n[SKIP] Snipe-IT integration tests")
        if not SNIPE_AVAILABLE:
            print("       Reason: SNIPE_API_TOKEN is missing")
        if not INTEGRATION_TESTS:
            print("       Reason: HYDRA_INTEGRATION_TESTS != '1'")
    
    # Summary
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