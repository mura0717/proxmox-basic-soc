""" Removes all assets for clean start. """

import os
import sys
from dotenv import load_dotenv
import urllib3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
# Only for testing when self-signed certs are used.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from crud.assets import AssetService

load_dotenv()

asset_service = AssetService()
assets = asset_service.get_all(limit=10000, refresh_cache=True)

if assets != []:
    print("All assets are being deleted...")
    for asset in assets:
        asset_service.delete_by_name(asset['name'])
    print("Asset deletion completed. But might need to rerun due to Rate Limiting.")
else:
    print("There are no assets to delete.")
 