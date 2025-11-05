"""Base CRUD service for Snipe-IT entities"""

import os
import sys
import subprocess
from typing import Dict, List, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.api_client import make_api_request
from assets_sync_library.text_utils import normalize_for_comparison, normalize_for_display
from snipe_db.snipe_db_connection import SnipeItDbConnection

class BaseCRUDService:
    """Base class for CRUD operations on Snipe-IT entities"""
    
    def __init__(self, endpoint: str, entity_name: str):
        """
        Initialize base CRUD service
        
        Args:
            endpoint: API endpoint (e.g., '/api/v1/fields')
            entity_name: Human-readable entity name (e.g., 'field')
        """
        self.endpoint = endpoint
        self.entity_name = entity_name
        self._cache = {}
    
    def get_all(self, limit: int = 500, refresh_cache: bool = False) -> List[Dict]:
        """Get all entities"""
        if not refresh_cache and 'all' in self._cache:
            return self._cache['all']
        response = make_api_request("GET", self.endpoint, params={"limit": limit})
        if response:
            data = response.json().get("rows", [])
            self._cache['all'] = data
            return data
        return []
    
    def get_by_id(self, entity_id: int) -> Optional[Dict]:
        """Get entity by ID"""
        response = make_api_request("GET", f"{self.endpoint}/{entity_id}")
        return response.json() if response else None
    
    def get_by_name(self, name: str) -> Optional[Dict]:
        """Get entity by name (normalized)"""
        if not name:
            return None
        normalized_search_name = normalize_for_comparison(name)
        all_entities = self.get_all()
        for entity in all_entities:
            entity_name = entity.get('name')
            if not entity_name:
                continue
            normalized_entity_name = normalize_for_comparison(entity_name)
            if normalized_entity_name == normalized_search_name:
                return entity
        return None
    
    def create(self, data: Dict) -> Optional[Dict]:
        """Create new entity"""
        if not data:
            print(f"Cannot create {self.entity_name}: No data provided")
            return None
        if 'name' in data:
            data['name'] = normalize_for_display(data['name'])
        if 'model_number' in data:
            data['model_number'] = normalize_for_display(data['model_number'])
    
        response = make_api_request("POST", self.endpoint, json=data)
        if not response:
            return None
        try:
            js = response.json()
            if isinstance(js, dict):
                if js.get("status") == "success":
                    self._cache.clear()
                    return js.get("payload", js)
                elif js.get("status") == "error":
                    print(f"[CREATE ERROR] {self.entity_name}: {js.get('messages')}")
                    self._cache.clear() 
                    return None
                
            return js
        except Exception as e:
            self._cache.clear() 
            print(f"[CREATE ERROR] Failed to parse response: {e}")
            return None

    def update(self, entity_id: int, data: Dict) -> Optional[Dict]:
        """Update entity by ID"""
        response = make_api_request("PATCH", f"{self.endpoint}/{entity_id}", json=data)
        if not response:
            return None
        js = response.json()
        if isinstance(js, dict) and js.get("status") == "error":
            print(f"[UPDATE ERROR] {self.entity_name}: {js.get('messages')}")
            return None
        self._cache.clear()
        return js
    
    def delete(self, entity_id: int) -> bool:
        """Delete entity by ID"""
        response = make_api_request("DELETE", f"{self.endpoint}/{entity_id}")
        if response and response.ok:
            self.get_all(refresh_cache=True) # Force a refresh of the cache on the next 'get_all' call.

            return True
        return False
    
    def create_if_not_exists(self, data: Dict) -> bool:
        """
        Create an entity only if it doesn't already exist by name.
        Returns True if a new entity was created, False otherwise.
        """
        name = data.get('name')
        if not name:
            print(f"Error: No name provided for {self.entity_name}")
            return False
        
        if self.get_by_name(name):
            print(f"{self.entity_name.title()} '{name}' already exists")
            return False
        
        result = self.create(data)
        if result:
            print(f"Created {self.entity_name}: {name}")
            return True
        return False
    
    def get_or_create(self, data: Dict) -> Optional[Dict]:
        """
        Get an entity by name, or create it if it doesn't exist.
        Returns the entity dictionary (either found or newly created).
        """
        name = data.get('name')
        if not name:
            print(f"Error: No name provided for {self.entity_name}")
            return None
        
        existing = self.get_by_name(name)
        if existing:
            return existing
        
        return self.create(data)
    
    def delete_by_name(self, name: str) -> bool:
        """Delete entity by name"""
        entity = self.get_by_name(name)
        if entity:
            return self.delete(entity['id'])
        return False
    
    def get_map(self, key: str = 'name', value: str = 'id') -> Dict:
        """Get dictionary mapping of entities"""
        all_entities = self.get_all()
        return {entity.get(key): entity.get(value) for entity in all_entities}
    
    @staticmethod
    def truncate():
        """
        Truncates all relevant Snipe-IT tables for a clean reset.
        WARNING: This is a destructive operation that deletes ALL data in these tables.
        """
        db_manager = SnipeItDbConnection()
        connection = None
        tables_to_truncate = [
            'assets', 'models', 'manufacturers', 'categories', 'custom_fieldsets',
            'custom_fields', 'status_labels', 'locations', 'accessories',
            'components', 'consumables', 'licenses'
        ]
        print("\n--- TRUNCATING DATABASE TABLES ---")
        print("WARNING: This will permanently delete all data from specified tables.")

        try:
            connection = db_manager.db_connect()
            if not connection:
                print("✗ Could not proceed with truncate due to database connection failure.")
                return

            with connection.cursor() as cursor:
                print("  -> Disabling foreign key checks...")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")

                for table in tables_to_truncate:
                    print(f"  -> Truncating table: {table}...")
                    cursor.execute(f"TRUNCATE TABLE `{table}`;")

                print("  -> Re-enabling foreign key checks...")
                cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

            connection.commit()
            print("✓ Database truncation complete.")
        except Exception as e:
            print(f"✗ An unexpected error occurred during database truncation: {e}")
        finally:
            if connection:
                db_manager.db_disconnect(connection)
        
    
    @staticmethod
    def purge_deleted_via_database():
        """
        Purges all soft-deleted records by calling the official Snipe-IT artisan command.
        """
        snipe_it_path = os.getenv("SNIPE_IT_APP_PATH", "/var/www/snipe-it")
        if not os.path.isdir(snipe_it_path):
            print(f"✗ ERROR: Snipe-IT path '{snipe_it_path}' not found. Cannot run purge command.")
            print("  Please set SNIPE_IT_APP_PATH in your .env file if it's in a non-standard location.")
            return

        command = ['php', 'artisan', 'snipeit:purge', '--force']
        
        print(f"-> Running official Snipe-IT purge command: {' '.join(command)}")
        try:
            # We run the command from within the Snipe-IT directory
            # We pipe 'yes' to stdin to automatically confirm the prompt.
            result = subprocess.run(
                command,
                cwd=snipe_it_path,
                capture_output=True, text=True, check=True,
                input='yes\n'
            )
            print("  " + result.stdout.strip().replace('\n', '\n  '))
            print("✓ Purge command completed successfully.")
        except FileNotFoundError:
            print("✗ ERROR: 'php' command not found. Is PHP installed and in your system's PATH?")
        except subprocess.CalledProcessError as e:
            print(f"✗ An error occurred while running the purge command:")
            print(f"  Return Code: {e.returncode}")
            print(f"  Output:\n{e.stdout}")
            print(f"  Error Output:\n{e.stderr}")
        
                    