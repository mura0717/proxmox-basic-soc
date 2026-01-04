""" Removes all assets for a clean start. """

import urllib3

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from proxmox_soc.snipe_it.snipe_api.services.assets import AssetService
from proxmox_soc.snipe_it.snipe_api.services.crudbase import CrudBaseService

asset_service = AssetService()
assets = asset_service.get_all(limit=10000, refresh_cache=True)

if assets != []:
    print("Asset deletion started...")
    for asset in assets:
        asset_service.delete(asset['id'])
        print(f"Soft-deleted asset: {asset.get('name', 'Unnamed')} (ID: {asset['id']})")
    print("Soft-deletion of assets completed.")
    print("\n--- Purging soft-deleted records from the database ---")
    CrudBaseService.purge_deleted_via_database()
    print("Purging completed.")
else:
    print("There are no assets to delete.")
 