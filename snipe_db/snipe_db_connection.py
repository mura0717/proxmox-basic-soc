#!/usr/bin/env python3
"""
Snipe-IT DB connection.
"""

import os
import pymysql
from dotenv import load_dotenv

class SnipeItDbConnection():
    
    def __init__(self):
        load_dotenv()
        self.db_host = os.getenv("DB_HOST", "snipeit-db")
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
            # If connection failed, return None
            return None
    
    def db_disconnect(self, connection):
        """Closes the database connection."""
        if connection:
            connection.close()
            print("✓ Database connection closed")
