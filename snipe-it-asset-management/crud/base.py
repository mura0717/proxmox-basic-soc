"""Base CRUD service for Snipe-IT entities"""


import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from typing import Dict, List, Optional, Any
from snipe_api.api_client import make_api_request

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
    
    def get_all(self, limit: int = 5000, refresh_cache: bool = False) -> List[Dict]:
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
        """Get entity by name"""
        all_entities = self.get_all()
        for entity in all_entities:
            if entity.get('name') == name:
                return entity
        return None
    
    def create(self, data: Dict) -> Optional[Dict]:
        """Create new entity"""
        response = make_api_request("POST", self.endpoint, json=data)
        if response:
            self._cache.clear()  # Clear cache on modification
            return response.json()
        return None
    
    def update(self, entity_id: int, data: Dict) -> Optional[Dict]:
        """Update entity by ID"""
        response = make_api_request("PATCH", f"{self.endpoint}/{entity_id}", json=data)
        if response:
            self._cache.clear()
            return response.json()
        return None
    
    def delete(self, entity_id: int) -> bool:
        """Delete entity by ID"""
        response = make_api_request("DELETE", f"{self.endpoint}/{entity_id}")
        if response and response.ok:
            self._cache.clear()
            return True
        return False
    
    def create_if_not_exists(self, data: Dict) -> bool:
        """Create entity only if it doesn't exist"""
        name = data.get('name')
        if not name:
            print(f"Error: No name provided for {self.entity_name}")
            return False
        
        if self.get_by_name(name):
            # print(f"{self.entity_name.title()} '{name}' already exists")
            return False
        
        result = self.create(data)
        if result:
            print(f"Created {self.entity_name}: {name}")
            return True
        return False
    
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