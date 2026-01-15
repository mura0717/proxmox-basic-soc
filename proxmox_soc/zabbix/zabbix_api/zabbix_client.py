"""
Shared Zabbix API Client for making JSON-RPC calls.
"""

import requests
from typing import Dict, Any, Optional
from proxmox_soc.config.hydra_settings import ZABBIX

class ZabbixClient:
    """
    Handles authentication and JSON-RPC communication with Zabbix.
    """
    
    def __init__(self):
        self.url = ZABBIX.zabbix_url
        self.user = ZABBIX.zabbix_username
        self.password = ZABBIX.zabbix_pass
        self.req_id = 0
        self.auth: Optional[str] = None
        self._authenticate()

    def _authenticate(self):
        """Authenticate and store token."""
        try:
            # Login call does not require auth token
            self.auth = self._rpc_call("user.login", {"username": self.user, "password": self.password}, require_auth=False)
        except Exception as e:
            print(f"[Zabbix Client] Authentication failed: {e}")

    def call(self, method: str, params: Dict[str, Any], require_auth: bool = True) -> Any:
        """Public method to make API calls."""
        return self._rpc_call(method, params, require_auth)

    def _rpc_call(self, method: str, params: Dict[str, Any], require_auth: bool = True) -> Any:
        """Internal RPC handler."""
        self.req_id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "params": params,
            "id": self.req_id
        }
        
        if require_auth:
            if not self.auth:
                raise RuntimeError("Zabbix client not authenticated")
            payload["auth"] = self.auth

        headers = {"Content-Type": "application/json"}
        response = requests.post(self.url, json=payload, headers=headers, verify=False, timeout=30)
        
        data = response.json()
        if "error" in data:
            error_msg = data['error'].get('data') or data['error'].get('message')
            raise RuntimeError(f"Zabbix API Error ({method}): {error_msg}")
            
        return data.get("result")