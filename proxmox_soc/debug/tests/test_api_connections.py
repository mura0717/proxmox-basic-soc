#!/usr/bin/env python3
"""
Central API Connectivity Tester
Checks connections and authentication for Snipe-IT, Zabbix, and Wazuh (API & Indexer).
"""

import os
import requests
import urllib3
from pathlib import Path

# Suppress insecure request warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from proxmox_soc.config.settings import SNIPE, ZABBIX, WAZUH
from proxmox_soc.snipe_it.snipe_api.snipe_client import make_api_request

CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "config" / "settings.py"

def print_status(service, status, message):
    symbol = "✓" if status else "✗"
    color = "\033[92m" if status else "\033[91m"
    reset = "\033[0m"
    print(f"[{color}{symbol}{reset}] {service}: {message}")

def test_snipe():
    print("\n--- Testing Snipe-IT ---")
    print(f"Target URL: {SNIPE.snipe_url}")
    try:
        # Test connectivity and auth by fetching current user info
        # Using make_api_request ensures we test the exact logic used by the app
        response = make_api_request("GET", "/api/v1/users/me", timeout=10)
        
        if response and response.status_code == 200:
            data = response.json()
            user = data.get('username', 'Unknown')
            print_status("Snipe-IT API", True, f"Connected as '{user}'")
        else:
            status = response.status_code if response else "No Response"
            print_status("Snipe-IT API", False, f"HTTP {status}")
    except Exception as e:
        print_status("Snipe-IT API", False, f"Connection Error: {e}")

def test_zabbix():
    print("\n--- Testing Zabbix ---")
    print(f"Target URL: {ZABBIX.zabbix_url}")
    
    # 1. Test Version (No Auth required usually for apiinfo.version)
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "apiinfo.version",
            "params": [],
            "id": 1
        }
        response = requests.post(
            ZABBIX.zabbix_url,
            json=payload,
            verify=False,
            timeout=10
        )
        if response.status_code == 200:
            result = response.json()
            if 'result' in result:
                print_status("Zabbix Version", True, f"API Version {result['result']}")
            else:
                print_status("Zabbix Version", False, f"Unexpected response: {result}")
        else:
            print_status("Zabbix Version", False, f"HTTP {response.status_code}")
            if response.status_code == 404:
                print("    -> Hint: Zabbix URL might need '/zabbix' prefix (e.g., http://ip/zabbix/api_jsonrpc.php)")
    except Exception as e:
        print_status("Zabbix API", False, f"Connection Error: {e}")
        return

    # 2. Test Authentication
    try:
        payload = {
            "jsonrpc": "2.0",
            "method": "user.login",
            "params": {
                "username": ZABBIX.zabbix_username,
                "password": ZABBIX.zabbix_pass
            },
            "id": 2
        }
        
        response = requests.post(
            ZABBIX.zabbix_url,
            json=payload,
            verify=False,
            timeout=10
        )
        
        if response.status_code != 200:
            print_status("Zabbix Auth", False, f"HTTP {response.status_code}")
            return
            
        result = response.json()
        
        if 'result' in result:
            auth_token = result['result']
            print_status("Zabbix Auth", True, "Authentication Successful")
            
            # Logout
            logout_payload = {
                "jsonrpc": "2.0",
                "method": "user.logout",
                "params": [],
                "id": 3,
                "auth": auth_token
            }
            requests.post(ZABBIX.zabbix_url, json=logout_payload, verify=False)
            
        elif 'error' in result:
            error_msg = result['error'].get('data') or result['error'].get('message')
            print_status("Zabbix Auth", False, f"Auth Failed: {error_msg}")
            
    except Exception as e:
        print_status("Zabbix Auth", False, f"Error: {e}")

def test_wazuh():
    print("\n--- Testing Wazuh ---")
    print(f"API URL: {WAZUH.wazuh_api_url}")
    print(f"API User: {WAZUH.wazuh_api_user}")
    
    # 1. Wazuh API
    try:
        # Wazuh API usually uses Basic Auth to get a JWT token
        auth = (WAZUH.wazuh_api_user, WAZUH.wazuh_api_pass)
        
        # Attempt to authenticate
        response = requests.get(
            f"{WAZUH.wazuh_api_url}/security/user/authenticate",
            auth=auth,
            verify=False,
            timeout=10
        )
        
        if response.status_code == 200:
            token = response.json().get('data', {}).get('token')
            print_status("Wazuh API", True, "Authentication Successful")
            
            # Optional: Get Manager Info using the token
            if token:
                headers = {"Authorization": f"Bearer {token}"}
                info_resp = requests.get(f"{WAZUH.wazuh_api_url}/manager/info", headers=headers, verify=False)
                if info_resp.status_code == 200:
                    ver = info_resp.json().get('data', {}).get('version')
                    print(f"    > Manager Version: {ver}")
        else:
            print_status("Wazuh API", False, f"HTTP {response.status_code} - {response.text[:100]}")
            
    except Exception as e:
        print_status("Wazuh API", False, f"Connection Error: {e}")

    # 2. Wazuh Ingestion (Log File Check) - REPLACED INDEXER CHECK
    print(f"Ingestion Method: Log File + Agent")
    print(f"Log Path: {WAZUH.event_log}")
    
    try:
        # Check if directory exists
        log_dir = WAZUH.event_log.parent
        if not log_dir.exists():
             print_status("Wazuh Log", False, f"Directory does not exist: {log_dir}")
             return

        # Check write permissions
        if os.access(log_dir, os.W_OK):
             print_status("Wazuh Log", True, "Log directory is writable")
        else:
             print_status("Wazuh Log", False, "Permission Denied writing to log directory")
             
        print("    ! Note: Direct Indexer connection skipped (Using Log+Agent method)")

    except Exception as e:
        print_status("Wazuh Log", False, f"Error: {e}")

if __name__ == "__main__":
    print("=== Central API Connectivity Test ===")
    print(f"Loaded Settings from: {CONFIG_PATH}")
    
    test_snipe()
    test_zabbix()
    test_wazuh()