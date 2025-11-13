""" Removes all models for a clean start. """

import os
import sys
import urllib3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
# Only for testing when self-signed certs are used.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from crud.base import BaseCRUDService

def truncate_table(table_name: str):
    """Finds and deletes the specified category."""
    
    crud_service = BaseCRUDService()

    print(f"Searching for table: '{table_name}'...")
    table_to_truncate = crud_service.get_by_name(table_name)

    if not table_to_truncate:
        print(f"✗ table '{table_name}' not found. Nothing to do.")
        return

    print(f"✓ Found table '{table_name}' (ID: {table_to_truncate['id']}).")

    if crud_service.truncate_by_name(table_name):
        print(f"✓ Successfully truncated table: '{table_name}'")
    else:
        print(f"✗ Failed to truncate table '{table_name}'")

if __name__ == "__main__":
    TARGET_TABLE = "custom_fieldsets"
    truncate_table(TARGET_TABLE)