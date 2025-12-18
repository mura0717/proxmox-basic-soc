""" Removes all models for a clean start. """

import urllib3

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from proxmox_soc.snipe_it.snipe_api.services.crudbase import BaseCRUDService

def truncate_table(table_name: str):
    """
    Calls the centralized truncate method from BaseCRUDService.
    """
    if not table_name or not table_name.strip():
        print("✗ Error: No table name provided.")
        return
    
    BaseCRUDService.truncate_tables([table_name])

if __name__ == "__main__":
    TABLES_TO_TRUNCATE = ["assets"]
    BaseCRUDService.truncate_tables(TABLES_TO_TRUNCATE)