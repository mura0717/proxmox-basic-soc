#!/usr/bin/env python3

"""
A simple Nmap scanner class for demonstration and testing purposes.
This class is not intended for production use.
"""

import os
import sys
import subprocess
import nmap
import json
from datetime import datetime

class SimpleNmapScanner:

    # Auto-elevate to root if needed, using the robust logic from nmap_scanner.py
    if os.geteuid() != 0:
        #---DEBUG---
        user_euid = os.geteuid()
        command_to_run = ['sudo', sys.executable] + sys.argv
        print(f"\n[DEBUG] - The command being passed to sudo is: {' '.join(command_to_run)}\nThe user euid is: {user_euid}\n")
        
        test_cmd = ['sudo', '-n', sys.executable, '-c', 'exit(0)']
        result = subprocess.run(test_cmd, capture_output=True, timeout=5)
        can_sudo = result.returncode == 0

        if can_sudo:
            try:
                print("Attempting to elevate to root privileges for scan...")
                subprocess.run(['sudo', sys.executable] + sys.argv, check=True)
                sys.exit(0)
            except (FileNotFoundError, subprocess.CalledProcessError) as e:
                print(f"\nERROR: Either sudo failed or scan failed: {e}")
                sys.exit(1)
        else:
            print("\nERROR: Root privileges are required for this scan.")
            print("This script cannot auto-elevate because 'sudo' requires a password.")
            print(f"Please run it manually with: sudo {sys.executable} {' '.join(sys.argv)}")
            sys.exit(1)

    if os.geteuid() != 0:
        print("✗ Failed to run with root privilege.")

    nm = nmap.PortScanner()
    def __init__(self):
        pass


    def clear_logs(self, source: str):
        """Clears all log files for a specific source."""
        if not self._should_log(source): return
        
        source_files = self.log_files.get(source.lower(), {})
        for file_path in source_files.values():
            with open(file_path, "w", encoding="utf-8") as f: f.write("")

    def log_parsed_asset_data(self, source: str, data: list):
        if not self._should_log(source): return
        log_path = self._get_log_path(source, 'parsed')
        if not log_path: return
        
        message = f"\n--- PARSED ASSET DATA ---\n" + \
                  f"Found {len(data)} assets.\n" + \
                  json.dumps(data, indent=2) + "\n" + "-"*50
        self._write_log(message, log_path)
        
        
    def log_sync_summary(self, source: str, results: dict):
        if not self._should_log(source): return
        log_path = self._get_log_path(source, 'summary')
        if not log_path: return
        
        message = f"\n--- SYNC SUMMARY ---\n" + \
                  f"Created: {results.get('created', 0)}\n" + \
                  f"Updated: {results.get('updated', 0)}\n" + \
                  f"Failed:  {results.get('failed', 0)}\n" + "-"*50
        self._write_log(message, log_path)

    def log_final_payload(self, scan_type: str, action: str, asset_name: str, payload: dict):
        """Logs the final payload being sent to the Snipe-IT API."""
        if not self._should_log(scan_type): return
        log_path = self._get_log_path(scan_type, 'final_payload')
        if not log_path: return

        message = f"\n--- FINAL PAYLOAD | Action: {action.upper()} | Asset: {asset_name} ---\n" + \
                  json.dumps(payload, indent=2, default=str) + "\n" + "-"*50
        self._write_log(message, log_path)

    def _write_log(self, message: str, log_file: str):
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        try:
            with open(log_file, "a", encoding="utf-8") as f: f.write(log_entry + "\n")
        except IOError as e:
            print(f"Warning: Could not write to log file {log_file}: {e}")

    # --- CONFIGURATION ---
    # Set this to 'discovery' or 'detailed' to choose the scan type.
    SCAN_TYPE = 'discovery'
    ip_addr = '192.168.1.1'
    ip_addr_range = '192.168.1.0/24'

    # --- Scan Profiles ---
    SCAN_PROFILES = {
        'discovery': {
            'args': '-sn',  # Ping scan, no ports
            'ports': None
        },
        'detailed': {
            'args': '-v -sS -sV -O -A --osscan-guess',
            'ports': '1-1024'
        }
    }

    print("Starting Nmap scan...")

    # --- Run Scan ---
    profile = SCAN_PROFILES[SCAN_TYPE]
    nm.scan(hosts=ip_addr_range, ports=profile['ports'], arguments=profile['args'])

    assets = []
    for host in nm.all_hosts():
        if nm[host].state() != 'up':
            continue

        # --- Parse Host Data ---
        if SCAN_TYPE == 'discovery':
            asset = {
                'ip': host,
                'hostname': nm[host].hostname() or 'Unknown',
                'mac': nm[host]['addresses'].get('mac', 'Unknown'),
                'state': nm[host].state(),
                'manufacturer': list(nm[host].get('vendor', {}).values())[0] if nm[host].get('vendor') else 'Unknown'
            }
            assets.append(asset)

        elif SCAN_TYPE == 'detailed':
            # Safely get OS match and vendor info
            os_match = nm[host].get('osmatch', [])
            vendor = nm[host].get('vendor', {})
            
            asset = {
                'ip': host,
                'hostname': nm[host].hostname() or 'Unknown',
                'os': os_match[0]['name'] if os_match else 'Unknown',
                'mac': nm[host]['addresses'].get('mac', 'Unknown'),
                'state': nm[host].state(),
                'manufacturer': list(vendor.values())[0] if vendor else 'Unknown',
                'protocols': {},
                # The following fields are kept for compatibility but parsed safely
                'manufacturer': list(nm[host]['vendor'].values())[0] if 'vendor' in nm[host] else 'Unknown',
                'product_113': nm[host]['tcp'][0]['product'] if 'product' in nm[host] else 'Unknown',
                'product_443': nm[host]['tcp'][1]['product'] if 'product' in nm[host] else 'Unknown',
                'version_113': nm[host]['tcp'][0]['version'] if 'version' in nm[host] else 'Unknown',
                'version_443': nm[host]['tcp'][1]['version'] if 'version' in nm[host] else 'Unknown',
                'extra_info_113': nm[host]['tcp'][0]['extrainfo'] if 'extrainfo' in nm[host] else 'Unknown',
                'extra_info_443': nm[host]['tcp'][1]['extrainfo'] if 'extrainfo' in nm[host] else 'Unknown',
                'manufacturer': list(nm[host].get('vendor', {}).values())[0] if nm[host].get('vendor') else 'Unknown'
            }
            # Safely parse protocol and port information
            for proto in nm[host].all_protocols():
                asset['protocols'][proto] = []
                for port, port_info in nm[host][proto].items():
                    asset['protocols'][proto].append({
                        'port': port,
                        'state': port_info.get('state', 'unknown'),
                        'product': port_info.get('product', ''),
                        'version': port_info.get('version', ''),
                        'extrainfo': port_info.get('extrainfo', '')
                    })
            assets.append(asset)
            
    print("Scan Info:", nm.scaninfo())
    print("Assets found:", len(assets))
    for asset in assets:
        print(asset)
    print("All scanned hosts:", nm.all_hosts())
    
__main__ = "__main__"
if __name__ == __main__:
    scanner = SimpleNmapScanner()
    scanner.run_scan()
    