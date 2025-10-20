#!/usr/bin/env python3

"""
Simple Nmap scan for testing.
"""

import os
import sys
import subprocess
import nmap

# Auto-elevate to root if needed, using the robust logic from nmap_scanner.py
if os.geteuid() != 0:
    #---DEBUG---
    user_euid = os.geteuid()
    command_to_run = ['sudo', sys.executable] + sys.argv
    print(f"\n---DEBUG---\nThe exact command being passed to sudo is: {' '.join(command_to_run)}\nAnd the user euid is: {user_euid}\n")
    
    test_cmd = ['sudo', '-n', sys.executable, '-c', 'exit(0)']
    result = subprocess.run(test_cmd, capture_output=True, timeout=5)
    can_sudo = result.returncode == 0

    if can_sudo:
        try:
            print("Attempting to elevate to root privileges for scan...")
            subprocess.run(['sudo', sys.executable] + sys.argv, check=True)
            sys.exit(0)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"\nERROR: Failed to auto-elevate even with passwordless sudo rights: {e}")
            sys.exit(1)
    else:
        print("\nERROR: Root privileges are required for this scan.")
        print("This script cannot auto-elevate because 'sudo' requires a password.")
        print(f"Please run it manually with: sudo {sys.executable} {' '.join(sys.argv)}")
        sys.exit(1)

if os.geteuid() != 0:
    print("✗ Failed to run with root privilege.")

nm = nmap.PortScanner()

ip_addr = '192.168.1.176' 
ip_addr_range = '192.168.1.0/24'
ports = '1-1024'
tcp_scan_args = '-v -sS -sV -O'
udp_scan_args = '-v -sU'

print("Starting Nmap scan...")
nm.scan(ip_addr, ports, tcp_scan_args)

assets = []
for host in nm.all_hosts():
    if nm[host].state() == 'up':
        asset = {
            'ip': host,
            'os': nm[host]['osmatch'][0]['name'] if 'osmatch' in nm[host] else 'Unknown',
            'hostname': nm[host].hostname(),
            'mac': nm[host]['addresses'].get('mac', 'Unknown'),
            'state': nm[host].state(),
            'protocols': {}
        }
        for proto in nm[host].all_protocols():
            lport = nm[host][proto].keys()
            asset['protocols'][proto] = [{'port': port, 'state': nm[host][proto][port]['state']} for port in lport]
        assets.append(asset)
        
print("Scan Info:", nm.scaninfo())
print("Assets found:")
for asset in assets:
    print(asset)
print("All scanned hosts:", nm.all_hosts())