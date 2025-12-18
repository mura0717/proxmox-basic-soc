""" Removes all models for a clean start. """

import urllib3

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from proxmox_soc.snipe_it.snipe_api.services.models import ModelService
from proxmox_soc.snipe_it.snipe_api.services.crudbase import BaseCRUDService

model_service = ModelService()
models = model_service.get_all(limit=10000, refresh_cache=True)

if models != []:
    print("Model deletion started...")
    for model in models:
        model_service.delete(model['id'])
        print(f"Soft-deleted model: {model.get('name', 'Unnamed')} (ID: {model['id']})")
    print("Soft-deletion of models completed.")
    print("\n--- Purging soft-deleted records from the database ---")
    BaseCRUDService.purge_deleted_via_database()
else:
    print("There are no models to delete.")
 