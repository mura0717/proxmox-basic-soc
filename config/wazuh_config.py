"""
Central configuration - All traffic routes through reverse proxy
"""
import os
from pathlib import Path
from dataclasses import dataclass
from typing import Dict

from dotenv import load_dotenv
load_dotenv(Path(__file__).parent.parent / '.env')

# Reverse proxy address
PROXY_HOST = os.getenv('PROXY_HOST', '192.168.1.191')

@dataclass
class WazuhConfig:
    # Route through reverse proxy (SSL terminated at proxy)
    api_url: str = os.getenv('WAZUH_API_URL', f'https://{PROXY_HOST}:8030')
    indexer_url: str = os.getenv('WAZUH_INDEXER_URL', f'https://{PROXY_HOST}:8031')
    indexer_user: str = os.getenv('WAZUH_INDEXER_USER', 'admin')
    indexer_password: str = os.getenv('WAZUH_INDEXER_PASSWORD', '')
    api_user: str = os.getenv('WAZUH_API_USER', 'wazuh-wui')
    api_password: str = os.getenv('WAZUH_API_PASSWORD', '')
    event_log: Path = Path('/opt/diabetes/proxmox-basic-soc/logs/wazuh_events.jsonl')
    
WAZUH = WazuhConfig()