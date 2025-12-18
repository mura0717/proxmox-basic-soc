""" Removes all models for a clean start. """

import os
import sys
from dotenv import load_dotenv
import urllib3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
# Only for testing when self-signed certs are used.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from endpoints.models import ModelService
from endpoints.base import BaseCRUDService

load_dotenv()

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
 