""" Removes all models for a clean start. """

import urllib3

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from proxmox_soc.snipe_it.snipe_api.services.fieldsets import FieldsetService
from proxmox_soc.snipe_it.snipe_api.services.crudbase import BaseCRUDService

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
 