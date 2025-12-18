""" Removes all models for a clean start. """

import os
import sys
from dotenv import load_dotenv
import urllib3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
# Only for testing when self-signed certs are used.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from endpoints.fieldsets import FieldsetService
from endpoints.base import BaseCRUDService

load_dotenv()

fieldset_service = FieldsetService()
fieldsets = fieldset_service.get_all(limit=10000, refresh_cache=True)

if fieldsets != []:
    print("Fieldset deletion started...")
    for fieldset in fieldsets:
        fieldset_service.delete(fieldset['id'])
        print(f"Soft-deleted fieldset: {fieldset.get('name', 'Unnamed')} (ID: {fieldset['id']})")
    print("Soft-deletion of fieldsets completed.")
    print("\n--- Purging soft-deleted records from the database ---")
    BaseCRUDService.purge_deleted_via_database()
    print("Purging completed.")
else:
    print("There are no fieldsets to delete.")
 