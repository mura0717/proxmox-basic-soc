#!/usr/bin/env python3

import os
import sys
import subprocess
import nmap

if os.geteuid() != 0:
    print("Elevating to root privileges...")
    subprocess.call(['sudo', sys.executable] + sys.argv)
    sys.exit()

nm = nmap.PortScanner()

ip_addr = '192.168.1.83' 
ip_addr_range = '192.168.1.0/24'
ports = '1-1024'
tcp_scan_args = '-v -sS -T3'
udp_scan_args = '-v -sU'

print("Starting Nmap scan...")
nm.scan(ip_addr, ports, tcp_scan_args)

assets = []
for host in nm.all_hosts():
    if nm[host].state() == 'up':
        asset = {
            'ip': host,
            'hostname': nm[host].hostname(),
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