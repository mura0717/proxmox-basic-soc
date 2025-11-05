# Configuration and constants for Snipe-IT setup

import os
from dotenv import load_dotenv

# Load environment variables
config_path = "/opt/snipeit-sync/snipe-it-asset-management/.env"
load_dotenv(dotenv_path=config_path)

# Azure Configuration

AZURE_TENANT_ID= os.getenv("AZURE_TENANT_ID")
AZURE_CLIENT_ID= os.getenv("AZURE_CLIENT_ID")
AZURE_CLIENT_SECRET= os.getenv("AZURE_CLIENT_SECRET")

if not AZURE_TENANT_ID or not AZURE_CLIENT_ID or not AZURE_CLIENT_SECRET:
    raise RuntimeError("Azure credentials not configured in environment.")

#---DEBUG PRINT---
#print(f"AZURE_TENANT_ID: {AZURE_TENANT_ID} " + f"AZURE_CLIENT_ID: {AZURE_CLIENT_ID} " + f"AZURE_CLIENT_SECRET: {AZURE_CLIENT_SECRET}")