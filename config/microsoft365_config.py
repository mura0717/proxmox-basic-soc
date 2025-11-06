# Configuration and constants for Microsoft365 setup

import os
from dotenv import load_dotenv

# Load environment variables
config_path = "/opt/snipeit-sync/snipe-it-asset-management/.env"
load_dotenv(dotenv_path=config_path)

# Configuration

AZURE_TENANT_ID= os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID= os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET= os.getenv("AZURE_CLIENT_SECRET")

if not AZURE_TENANT_ID or not AZURE_CLIENT_ID or not AZURE_CLIENT_SECRET:
    raise RuntimeError("Azure credentials not configured in environment.")

#print(f"[DEBUG] AZURE_TENANT_ID: {AZURE_TENANT_ID} " + f"AZURE_CLIENT_ID: {AZURE_CLIENT_ID} " + f"AZURE_CLIENT_SECRET: {AZURE_CLIENT_SECRET}")

import os
import sys
from msal import ConfidentialClientApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class Microsoft365:
    """Microsoft365 API service"""
    
    def __init__(self):
        # Load credentials from environment
        self.tenant_id = AZURE_TENANT_ID
        self.client_id = AZURE_CLIENT_ID
        self.client_secret = AZURE_CLIENT_SECRET
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Azure credentials not configured in environment")
        
        self.graph_url = "https://graph.microsoft.com/v1.0"
        self.access_token = None
    
    def authenticate(self) -> bool:
        """Authenticate with Microsoft Graph API"""
        try:
            app = ConfidentialClientApplication(
                self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
                client_credential=self.client_secret
            )
            
            result = app.acquire_token_silent(
                ["https://graph.microsoft.com/.default"],
                account=None
            )
            
            if not result:
                result = app.acquire_token_for_client(
                    scopes=["https://graph.microsoft.com/.default"]
                )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                return True
            else:
                print(f"Authentication failed: {result.get('error_description')}")
                return False
                
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
        
