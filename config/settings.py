"""
Centralized Configuration for Hydra
"""
import os
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# 1. Load Environment Variables (Once)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# 2. Global Defaults
HYDRA_DEBUG = os.getenv('HYDRA_DEBUG', '0') == '1'
USE_PROXY = os.getenv('USE_PROXY', 'False').lower() in ('true', '1', 'yes')

# 3. Network Endpoints Configuration

# Proxy Host Configuration
PROXY_HOST = os.getenv('PROXY_HOST')

# Direct backend IPs
DIRECT_IPS = {
    'snipe': os.getenv('SNIPE_URL'),
    'zabbix': os.getenv('ZABBIX_URL'),
    'wazuh': os.getenv('WAZUH_API_URL'),
}

# Port mappings
PROXY_PORTS = {
    'snipe': os.getenv('SNIPE_PROXY_PORT'),
    'zabbix': os.getenv('ZABBIX_PROXY_PORT'),
    'wazuh_api': os.getenv('WAZUH_PROXY_PORT_API'),
    'wazuh_indexer': os.getenv('WAZUH_PROXY_PORT_INDEXER'),
}

DIRECT_PORTS = {
    'snipe': os.getenv('SNIPE_DIRECT_PORT'),
    'zabbix': os.getenv('ZABBIX_DIRECT_PORT'),
    'wazuh_api': os.getenv('WAZUH_DIRECT_PORT_API'),
    'wazuh_indexer': os.getenv('WAZUH_DIRECT_PORT_INDEXER'),
}

@dataclass
class SnipeConfig:
    snipe_api_key: str = os.getenv("SNIPE_API_TOKEN")
    verify_ssl: bool = os.getenv("VERIFY_SSL", "False").lower() in ('true', '1', 'yes')

    if USE_PROXY:
        url: str = os.getenv("SNIPE_URL", f"http://{PROXY_HOST}:{PROXY_PORTS['snipe']}").rstrip("/")
    else:
        url: str = os.getenv("SNIPE_URL", f"http://{DIRECT_IPS['snipe']}:{DIRECT_PORTS['snipe']}").rstrip("/")
    
    def __post_init__(self):
        if not self.snipe_api_key:
            raise RuntimeError("CRITICAL: SNIPE_API_TOKEN is missing from .env")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.snipe_api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

@dataclass
class ZabbixConfig:
    zabbix_user: str = os.getenv('ZABBIX_USER')
    zabbix_pass: str = os.getenv('ZABBIX_PASS')
    
    if USE_PROXY:
        url: str = os.getenv('ZABBIX_URL', f'http://{PROXY_HOST}:{PROXY_PORTS["zabbix"]}/zabbix/api_jsonrpc.php')
    else:
        url: str = os.getenv('ZABBIX_URL', f'http://{DIRECT_IPS["zabbix"]}:{DIRECT_PORTS["zabbix"]}/zabbix/api_jsonrpc.php')
        
    def __post_init__(self):
        # Auto-correct URL if /zabbix is missing (common config error)
        if self.url and '/api_jsonrpc.php' in self.url and '/zabbix/' not in self.url:
            self.url = self.url.replace('/api_jsonrpc.php', '/zabbix/api_jsonrpc.php')


@dataclass
class WazuhConfig:
    indexer_user: str = os.getenv('WAZUH_INDEXER_USER')
    indexer_password: str = os.getenv('WAZUH_INDEXER_PASSWORD')
    wazuh_user: str = os.getenv('WAZUH_API_USER')
    wazuh_pass: str = os.getenv('WAZUH_API_PASS')
    
    event_log: Path = Path('/opt/diabetes/proxmox-basic-soc/logs/wazuh_events.jsonl')
    
    if USE_PROXY:
        api_url: str = os.getenv('WAZUH_API_URL', f'https://{PROXY_HOST}:{PROXY_PORTS["wazuh_api"]}').rstrip('/')
        indexer_url: str = os.getenv('WAZUH_INDEXER_URL', f'https://{PROXY_HOST}:{PROXY_PORTS["wazuh_indexer"]}').rstrip('/')
    else:
        api_url: str = os.getenv('WAZUH_API_URL', f'https://{DIRECT_IPS["wazuh"]}:{DIRECT_PORTS["wazuh_api"]}').rstrip('/')
        indexer_url: str = os.getenv('WAZUH_INDEXER_URL', f'https://{DIRECT_IPS["wazuh"]}:{DIRECT_PORTS["wazuh_indexer"]}').rstrip('/')

    def __post_init__(self):
        if not self.wazuh_user or not self.wazuh_pass:
            print("WARNING: Wazuh API credentials (WAZUH_API_USER, WAZUH_API_PASSWORD) are missing from .env")


# 4. Singleton Instances
SNIPE = SnipeConfig()
ZABBIX = ZabbixConfig()
WAZUH = WazuhConfig()

if HYDRA_DEBUG:
    masked_key = SNIPE.snipe_api_key[:5] + "..." if SNIPE.snipe_api_key else "None"
    print(f"SNIPE_URL: {SNIPE.url} " + f"SNIPE_API_TOKEN: {masked_key} " + f"SSL_VERIFY: {SNIPE.verify_ssl}")
    print(f"ZABBIX_URL: {ZABBIX.url} " + f"ZABBIX_USER: {ZABBIX.zabbix_user} " + f"ZABBIX_PASS: {ZABBIX.zabbix_pass}")
    print(f"WAZUH_API_URL: {WAZUH.api_url} " + f"WAZUH_INDEXER_URL: {WAZUH.indexer_url}")