"""
Centralized Configuration for Hydra
"""
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict
from dotenv import load_dotenv

# 1. Load Environment Variables (Once)
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / '.env')

# 2. Global Defaults
HYDRA_DEBUG = os.getenv('HYDRA_DEBUG', '0') == '1'
USE_PROXY = os.getenv('USE_PROXY', 'False').lower() in ('true', '1', 'yes')
PROXY_HOST = os.getenv('PROXY_HOST')

# Direct backend IPs
HOST_IPS = {
    'snipe': os.getenv('SNIPE_HOST_IP'),
    'zabbix': os.getenv('ZABBIX_HOST_IP'),
    'wazuh': os.getenv('WAZUH_HOST_IP'),
}

# Port mappings
PROXY_PORTS = {
    'snipe': os.getenv('SNIPE_PROXY_PORT'),
    'zabbix': os.getenv('ZABBIX_PROXY_PORT'),
    'wazuh_api': os.getenv('WAZUH_PROXY_API_PORT'),
    'wazuh_indexer': os.getenv('WAZUH_PROXY_INDEXER_PORT'),
}

DIRECT_PORTS = {
    'snipe': os.getenv('SNIPE_DIRECT_PORT'),
    'zabbix': os.getenv('ZABBIX_DIRECT_PORT'),
    'wazuh_api': os.getenv('WAZUH_DIRECT_API_PORT'),
    'wazuh_indexer': os.getenv('WAZUH_DIRECT_INDEXER_PORT'),
}

@dataclass
class SnipeConfig:
    snipe_api_key: str = os.getenv("SNIPE_API_TOKEN")
    verify_ssl: bool = os.getenv("VERIFY_SSL", "False").lower() in ('true', '1', 'yes')
    snipe_url: str = field(init=False)
    
    def __post_init__(self):
        if not self.snipe_api_key:
            raise RuntimeError("CRITICAL: SNIPE_API_TOKEN is missing from .env")
        if USE_PROXY:
            host = PROXY_HOST
            port = PROXY_PORTS["snipe"]
        else:
            host = HOST_IPS["snipe"]
            port = DIRECT_PORTS["snipe"]
            
        self.snipe_url = f"http://{host}:{port}"

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.snipe_api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

@dataclass
class ZabbixConfig:
    zabbix_username: str = os.getenv('ZABBIX_USER')
    zabbix_pass: str = os.getenv('ZABBIX_PASS')
    zabbix_url: str = field(init=False)
    
    def __post_init__(self):
        if USE_PROXY:
            host = PROXY_HOST
            port = PROXY_PORTS["zabbix"]
        else:
            host = HOST_IPS["zabbix"]
            port = DIRECT_PORTS["zabbix"]
            
        self.zabbix_url = f"http://{host}:{port}/zabbix/api_jsonrpc.php"

@dataclass
class WazuhConfig:
    wazuh_api_user: str = os.getenv('WAZUH_API_USER')
    wazuh_api_pass: str = os.getenv('WAZUH_API_PASS')
    event_log: Path = Path(os.getenv('WAZUH_EVENT_LOG_PATH'))
    wazuh_api_url: str = field(init=False)
    wazuh_indexer_url: str = field(init=False)
    
    def __post_init__(self):
        if USE_PROXY:
            host = PROXY_HOST
            api_port = PROXY_PORTS['wazuh_api']
            idx_port = PROXY_PORTS['wazuh_indexer']
            
            self.wazuh_api_url = f"http://{host}:{api_port}"
            self.wazuh_indexer_url = f"http://{host}:{idx_port}"
        else:
            host = HOST_IPS['wazuh']
            api_port = DIRECT_PORTS['wazuh_api']
            idx_port = DIRECT_PORTS['wazuh_indexer']

            self.wazuh_api_url = f"https://{host}:{api_port}"
            self.wazuh_indexer_url = f"https://{host}:{idx_port}"

# 4. Singleton Instances
SNIPE = SnipeConfig()
ZABBIX = ZabbixConfig()
WAZUH = WazuhConfig()

if HYDRA_DEBUG:
    mode = "PROXY" if USE_PROXY else "DIRECT"
    masked_key = SNIPE.snipe_api_key[:5] + "..." if SNIPE.snipe_api_key else "None"
    print(f"--- CONFIG LOADED ({mode} MODE) ---")
    print(f"SNIPE_URL: {SNIPE.snipe_url} " + f"SNIPE_API_TOKEN: {masked_key} " + f"SSL_VERIFY: {SNIPE.verify_ssl}")
    print(f"ZABBIX_URL: {ZABBIX.zabbix_url} " + f"ZABBIX_USER: {ZABBIX.zabbix_username} " + f"ZABBIX_PASS: {ZABBIX.zabbix_pass}")
    print(f"WAZUH_API_URL: {WAZUH.wazuh_api_url} " + f"WAZUH_INDEXER_URL: {WAZUH.wazuh_indexer_url}" + f"WAZUH_API_USER: {WAZUH.wazuh_api_user} " + f"WAZUH_API_PASS: {WAZUH.wazuh_api_pass}")