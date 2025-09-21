# Configuration and constants for Snipe-IT setup

import os
from dotenv import load_dotenv

# Load environment variables
config_path = "/opt/snipeit-sync/.env"
load_dotenv(dotenv_path=config_path)

# API Configuration
SNIPE_URL = (os.getenv("SNIPE_URL") or "").rstrip("/")
SNIPE_API_TOKEN = os.getenv("SNIPE_API_TOKEN")
VERIFY_SSL = os.getenv("SSL_VERIFY")

if not SNIPE_URL or not SNIPE_API_TOKEN:
    raise RuntimeError("SNIPE_URL and SNIPE_API_TOKEN must be set.")

HEADERS = {
    "Authorization": f"Bearer {SNIPE_API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json",
}

#print(f"SNIPE_URL: {SNIPE_URL} " + f"SNIPE_API_TOKEN: {SNIPE_API_TOKEN} " + f"SSL_VERIFY: {VERIFY_SSL}")