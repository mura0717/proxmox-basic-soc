#!/usr/bin/env python3
"""
Test connecting snipe it database.
"""

import os
import sys
from dotenv import load_dotenv
import urllib3

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
# Only for testing when self-signed certs are used.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from snipe_db.snipe_db_connection import SnipeItDbConnection

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