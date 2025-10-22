""" Removes all categories for a clean start. """

import os
import sys
from dotenv import load_dotenv
import urllib3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
# Only for testing when self-signed certs are used.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from crud.categories import CategoryService
from crud.base import BaseCRUDService

load_dotenv()

category_service = CategoryService()
categories = category_service.get_all(limit=10000, refresh_cache=True)

if categories != []:
    print("Category deletion started...")
    for category in categories:
        category_service.delete_by_name(category['name'])
        print(f"Deleted asset: {category['name']}")
    print("Soft-deletion of categories completed.")
    print("\n--- Purging soft-deleted records from the database ---")
    # This makes the deletion permanent
    BaseCRUDService.purge_deleted_via_database()
else:
    print("There are no categories to delete.")
 