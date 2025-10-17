#!/usr/bin/env python3

import os
import requests
from dotenv import load_dotenv
import urllib3
import json
import time
import subprocess

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
