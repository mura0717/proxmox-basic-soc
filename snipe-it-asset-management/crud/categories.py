"""CRUD service for Snipe-IT categories"""

from crud.base import BaseCRUDService

class CategoryService(BaseCRUDService):
    """Service for managing categories"""
    
    def __init__(self):
        super().__init__('/api/v1/categories', 'category')