""" Removes all categories for a clean start. """

import os
import sys
import urllib3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from proxmox_soc.snipe_it.snipe_api.services.categories import CategoryService
from proxmox_soc.snipe_it.snipe_api.services.crudbase import BaseCRUDService

category_service = CategoryService()
categories = category_service.get_all(limit=10000, refresh_cache=True)

if categories != []:
    print("Category deletion started...")
    for category in categories:
        category_service.delete_by_name(category['name'])
        print(f"Deleted category: {category['name']}")
    print("Soft-deletion of categories completed.")
    print("\n--- Purging soft-deleted records from the database ---")
    BaseCRUDService.purge_deleted_via_database()
    print("Purging completed.")
else:
    print("There are no categories to delete.")
 