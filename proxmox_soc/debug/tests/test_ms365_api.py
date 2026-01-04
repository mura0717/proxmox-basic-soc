"""
Test connecting to Microsoft365 (Intune, Teams, etc.) via API.
"""

import requests
from typing import Optional

from proxmox_soc.config.ms365_service import Microsoft365Service 

class MS365APTConnectionTester:
    """Microsoft Intune synchronization service"""
    
    def __init__(self):
        self.graph_url = "https://graph.microsoft.com/v1.0"
        self.ms365_service = Microsoft365Service() 
    
    def get_access_token(self) -> Optional[str]:
        """Ensure a valid access token is available and return it."""
        if not self.ms365_service.access_token:
            if not self.ms365_service.authenticate():
                print("Authentication failed via Microsoft365 helper.")
                return None
        return self.ms365_service.access_token
    
    def test_connection(self) -> bool:
        print("Testing connection to Microsoft365 API...")
        access_token = self.get_access_token()
        if not access_token:
            print("No access token available, cannot fetch Intune assets.")
            return []
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        url = f"{self.graph_url}/deviceManagement/managedDevices"
        
        try:
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            print("Successfully connected to MS365 API.")
            return True
        except requests.exceptions.RequestException as e:
            if 'response' in locals() and response is not None:
                    print(f"MS365 API Error - Response Status Code: {response.status_code}")
                    print(f"MS365 API Error - Response Body: {response.text}")
            return False

if __name__ == "__main__":
    ms365tester = MS365APTConnectionTester()
    ms365tester.test_connection()