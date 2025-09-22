#!/usr/bin/env python3
import nmap
nm = nmap.PortScanner()
nm.scan('192.168.1.0/24', '22-80')
print(nm.all_hosts())