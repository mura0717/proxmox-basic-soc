#!/usr/bin/env python3
"""
Test connecting snipe it database.
"""

import urllib3

# Suppress insecure request warnings for self-signed certs 
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from proxmox_soc.snipe_it.snipe_db.snipe_db_connection import SnipeItDbConnection

def main():
    db_manager = SnipeItDbConnection()
    connection = db_manager.db_connect()
    # The connection is only returned if successful
    if connection: 
        # If you were to do work, it would be here.
        print("Closing the test connection.")
        db_manager.db_disconnect(connection)
                
if __name__ == "__main__":
    main()