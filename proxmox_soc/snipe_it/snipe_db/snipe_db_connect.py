#!/usr/bin/env python3
"""
Snipe-IT DB connection.
"""

import os
import pymysql
from pathlib import Path
from sshtunnel import SSHTunnelForwarder
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(BASE_DIR / '.env')

class SnipeItDbConnection():
    
    def __init__(self):
        self.db_host = os.getenv("DB_HOST")
        self.db_user = os.getenv("DB_USER")
        self.db_pass = os.getenv("DB_PASS")
        self.db_name = os.getenv("DB_NAME")
        self.db_ssh_user = os.getenv("DB_SSH_USER")
        self.db_ssh_key_path = os.getenv("DB_SSH_KEY_PATH")
        self.tunnel = None

    def db_connect(self):
        """Establishes and returns a database connection via SSH tunnel if not local."""
        connection = None
        print("Attempting to connect to Snipe-IT database...")
        try:
            if self.db_ssh_user and self.db_ssh_key_path:
                print("Using SSH tunnel for database connection...")
                self.tunnel = SSHTunnelForwarder(
                    (self.db_host, 22),
                    ssh_username=self.db_ssh_user,
                    ssh_pkey=self.db_ssh_key_path,
                    remote_bind_address=('127.0.0.1', 3306)
                )
                self.tunnel.start()
                print(f"-> Tunnel established! Forwarding localhost:{self.tunnel.local_bind_port} -> {self.db_host}:3306")
                connection = pymysql.connect(host='127.0.0.1', user=self.db_user, password=self.db_pass, database=self.db_name, port=self.tunnel.local_bind_port, connect_timeout=5, cursorclass=pymysql.cursors.DictCursor)
                print("✓ Database connection successful")
                return connection
            else:
                print("Using local database connection...")
                connection = pymysql.connect(host=self.db_host, user=self.db_user, password=self.db_pass, database=self.db_name, connect_timeout=5,  cursorclass=pymysql.cursors.DictCursor)
                print("✓ Database connection successful")
                return connection
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
            self.close_tunnel()
            return None
    
    def db_disconnect(self, connection):
        """Closes the database connection."""
        if connection:
            connection.close()
            print("✓ Database connection closed")
        self.close_tunnel()

    def close_tunnel(self):
        """Safely closes the SSH tunnel."""
        if self.tunnel:
            self.tunnel.stop()
            self.tunnel = None
            print("-> SSH Tunnel closed")