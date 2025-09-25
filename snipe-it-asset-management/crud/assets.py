"""CRUD service for Snipe-IT assets"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crud.base import BaseCRUDService

class AssetService(BaseCRUDService):
    """Service for managing categories"""
    
    def __init__(self):
        super().__init__('/api/v1/hardware', 'hardware')