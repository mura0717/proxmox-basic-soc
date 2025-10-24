"""Base CRUD service for Snipe-IT entities"""

import os
import sys
import re
import pymysql
from typing import Dict, List, Optional
from dotenv import load_dotenv

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.api_client import make_api_request
from assets_sync_library.text_utils import normalize_for_comparison, normalize_for_display

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
    
    def purge_deleted_via_database():
        """Directly purge soft-deleted records from database"""
        load_dotenv()
    
        DB_HOST = os.getenv("DB_HOST")
        DB_USER = os.getenv("DB_USER")
        DB_PASS = os.getenv("DB_PASS")
        DB_NAME = os.getenv("DB_NAME")
        
        try:
            connection = pymysql.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME)
            with connection.cursor() as cursor:
                tables_to_purge =[
                'assets',
                'categories',
                'custom_fieldsets',
                'custom_fields',
                'status_labels',
                'locations',
                'manufacturers',
                'models'
                ]
            for table in tables_to_purge:
                    cursor.execute(f"DELETE FROM {table} WHERE deleted_at IS NOT NULL")
                    deleted_count = cursor.rowcount
                    if deleted_count > 0:
                        print(f"  ✓ Purged {deleted_count} records from {table}")
                
            connection.commit()
            print("✓ Database purge complete")
                
        except Exception as e:
            print(f"✗ Database connection failed: {e}")
        finally:
            if 'connection' in locals():
                connection.close()        
                    