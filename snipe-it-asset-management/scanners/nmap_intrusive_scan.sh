#!/bin/bash

# Nmap command to perform an inventory scan
# It's recommended to run this during off-hours to minimize network impact.

/usr/bin/sudo /usr/bin/nmap -sV -O -oX /home/kaan/nmap_scans/inventory.xml 192.168.1.0/24
