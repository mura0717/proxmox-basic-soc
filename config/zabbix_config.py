"""
Central configuration - All traffic routes through reverse proxy
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict

from dotenv import load_dotenv

env_config_path = os.getenv("ENV_FILE_PATH")
load_dotenv(dotenv_path=env_config_path)

# Reverse proxy address
PROXY_HOST = os.getenv('PROXY_HOST')

@dataclass
class ZabbixConfig:
    # Route through reverse proxy
    url: str = os.getenv('ZABBIX_URL', f'http://{PROXY_HOST}:8020')
    user: str = os.getenv('ZABBIX_USER', '')
    password: str = os.getenv('ZABBIX_PASS', '')
    
# Singleton instance
ZABBIX = ZabbixConfig()