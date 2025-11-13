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
    """
    Calls the centralized truncate method from BaseCRUDService.
    """
    if not table_name or not table_name.strip():
        print("✗ Error: No table name provided.")
        return
    
    BaseCRUDService.truncate_tables([table_name])

if __name__ == "__main__":
    TABLES_TO_TRUNCATE = [
        "assets",
        "action_logs",      # General activity logs, can contain asset info.
        "asset_logs",       # Specifically for asset checkin/checkout history.
        "maintenances"      # Asset maintenance records.
    ]
    BaseCRUDService.truncate_tables(TABLES_TO_TRUNCATE)