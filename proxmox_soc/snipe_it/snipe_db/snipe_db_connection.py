#!/usr/bin/env python3
"""
Snipe-IT DB connection.
"""

import os
import pymysql
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / '.env')

class SnipeItDbConnection():
    
    def __init__(self):
        self.db_host = os.getenv("DB_HOST")
        self.db_user = os.getenv("DB_USER")
        self.db_pass = os.getenv("DB_PASS")
        self.db_name = os.getenv("DB_NAME")
    
    def db_connect(self):
        """Establishes and returns a database connection."""
        connection = None
        try:
            connection = pymysql.connect(host=self.db_host, user=self.db_user, password=self.db_pass, database=self.db_name)
            print("✓ Database connection successful")
            return connection
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            return None
    
    def db_disconnect(self, connection):
        """Closes the database connection."""
        if connection:
            connection.close()
            print("✓ Database connection closed")
