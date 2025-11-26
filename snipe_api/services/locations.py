"""CRUD service for Snipe-IT locations"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.services.crudbase import BaseCRUDService

class LocationService(BaseCRUDService):
    """Service for managing locations"""
    
    def __init__(self):
        super().__init__('/api/v1/locations', 'location')