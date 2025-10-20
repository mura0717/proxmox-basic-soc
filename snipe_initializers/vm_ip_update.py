#!/usr/bin/env python3

import os
import sys
import requests
from dotenv import load_dotenv
import urllib3
import json
import time
import subprocess

COMMAND = sys.argv[1] if len(sys.argv) > 1 else ''

if os.geteuid() != 0:
    cmd = ['sudo', sys.executable, '-c', 'exit(0)']
    result = subprocess.run(cmd, capture_output=True, timeout=5)
    can_sudo = result.returncode == 0

    if can_sudo:
        try:
            print("Attempting to elevate to root privileges for scan...")
            subprocess.run(['sudo', sys.executable] + sys.argv, check=True)
            sys.exit(0)
        except (FileNotFoundError, subprocess.CalledProcessError) as e:
            print(f"\nERROR: Failed to auto-elevate even with passwordless sudo rights: {e}")
            sys.exit(1)



""" Changing ip:

sudo php artisan key:generate

sudo nano /etc/nginx/sites-available/snipe-it
sudo systemctl restart nginx

sudo nano /var/www/snipe-it/.env
sudo nano /opt/snipeit-sync/snipe-it-asset-management/.env


cd /var/www/snipe-it/
sudo -u www-data php artisan config:clear
sudo -u www-data php artisan cache:clear
sudo -u www-data php artisan view:clear """
