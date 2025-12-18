"""CRUD service for Snipe-IT categories"""

from proxmox_soc.snipe_it.snipe_api.services.crudbase import BaseCRUDService

class CategoryService(BaseCRUDService):
    """Service for managing categories"""
    
    def __init__(self):
        super().__init__('/api/v1/categories', 'category')