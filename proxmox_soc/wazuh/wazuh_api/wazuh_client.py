"""
Shared Wazuh API Client.
"""

import requests
import urllib3
from typing import Dict, Any, Optional
from proxmox_soc.config.hydra_settings import WAZUH

# Suppress insecure request warnings for self-signed certs
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class WazuhClient:
    """
    Client for interacting with the Wazuh Manager API.
    Handles authentication (JWT) and basic requests.
    """
    
    def __init__(self):
        self.base_url = WAZUH.wazuh_api_url
        self.user = WAZUH.wazuh_api_user
        self.password = WAZUH.wazuh_api_pass
        self.token: Optional[str] = None
        self._authenticate()

    def _authenticate(self):
        """Obtain JWT token via Basic Auth."""
        try:
            auth = (self.user, self.password)
            response = requests.get(
                f"{self.base_url}/security/user/authenticate",
                auth=auth,
                verify=False,
                timeout=10
            )
            
            if response.status_code == 200:
                self.token = response.json().get('data', {}).get('token')
            else:
                print(f"[Wazuh Client] Auth failed: HTTP {response.status_code}")
                
        except Exception as e:
            print(f"[Wazuh Client] Authentication error: {e}")
            self.token = None

    def get(self, endpoint: str, params: Dict = None) -> Dict:
        """Make a GET request to the API."""
        return self._request("GET", endpoint, params=params)

    def post(self, endpoint: str, json: Dict = None) -> Dict:
        """Make a POST request to the API."""
        return self._request("POST", endpoint, json=json)

    def _request(self, method: str, endpoint: str, **kwargs) -> Dict:
        """Internal request handler with token injection."""
        if not self.token:
            # Try one re-auth attempt if needed, or raise error
            self._authenticate()
            if not self.token:
                raise RuntimeError("Wazuh Client not authenticated.")

        # Ensure endpoint starts with /
        if not endpoint.startswith("/"):
            endpoint = f"/{endpoint}"

        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        url = f"{self.base_url}{endpoint}"
        
        response = requests.request(
            method, 
            url, 
            headers=headers, 
            verify=False, 
            timeout=30, 
            **kwargs
        )
        
        response.raise_for_status()
        return response.json()