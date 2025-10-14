#!/usr/bin/env python3

import os
import sys
import subprocess
import nmap

if os.geteuid() != 0:
    print("Elevating to root privileges...")
    subprocess.call(['sudo', sys.executable] + sys.argv)
    #result = subprocess.run(['sudo', sys.executable] + sys.argv, check=True)
    sys.exit()

nm = nmap.PortScanner()

ip_addr = '192.168.1.1' 
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
print("All hosts:", nm.all_hosts())