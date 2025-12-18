"""CRUD service for Snipe-IT locations"""

from proxmox_soc.snipe_it.snipe_api.services.crudbase import BaseCRUDService

class LocationService(BaseCRUDService):
    """Service for managing locations"""
    
    def __init__(self):
        super().__init__('/api/v1/locations', 'location')