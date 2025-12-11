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
# Prioritize explicit path, fall back to relative path
env_path = os.getenv("ENV_FILE_PATH") or Path(__file__).resolve().parent.parent / '.env'
load_dotenv(dotenv_path=env_path)

# 2. Global Defaults
DEBUG = os.getenv('HYDRA_DEBUG', '0') == '1'
PROXY_HOST = os.getenv('PROXY_HOST', '192.168.1.191')

@dataclass
class SnipeConfig:
    url: str = os.getenv("SNIPE_URL", f"http://{PROXY_HOST}:8010").rstrip("/")
    api_key: str = os.getenv("SNIPE_API_TOKEN")
    verify_ssl: bool = os.getenv("VERIFY_SSL", "False").lower() in ('true', '1', 'yes')

    def __post_init__(self):
        if not self.api_key:
            raise RuntimeError("CRITICAL: SNIPE_API_TOKEN is missing from .env")

    @property
    def headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

@dataclass
class ZabbixConfig:
    url: str = os.getenv('ZABBIX_URL', f'http://{PROXY_HOST}:8020/api_jsonrpc.php')
    user: str = os.getenv('ZABBIX_USER')
    password: str = os.getenv('ZABBIX_PASS')

@dataclass
class WazuhConfig:
    api_url: str = os.getenv('WAZUH_API_URL', f'https://{PROXY_HOST}:8030')
    indexer_url: str = os.getenv('WAZUH_INDEXER_URL', f'https://{PROXY_HOST}:8031')
    indexer_user: str = os.getenv('WAZUH_INDEXER_USER')
    indexer_password: str = os.getenv('WAZUH_INDEXER_PASSWORD')
    api_user: str = os.getenv('WAZUH_API_USER')
    api_password: str = os.getenv('WAZUH_API_PASSWORD')
    event_log: Path = Path('/opt/diabetes/proxmox-basic-soc/logs/wazuh_events.jsonl')

# 3. Singleton Instances
SNIPE = SnipeConfig()
ZABBIX = ZabbixConfig()
WAZUH = WazuhConfig()