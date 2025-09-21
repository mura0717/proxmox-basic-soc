#!/usr/bin/env python3

import requests
import nmap

response = requests.get("https://httpbin.org/get")
nmap = nmap.PortScanner()

host = '192.168.1.86'
nmap.scan(host, '1-10')

#res_json = response.json()

print(nmap.command_line())