"""CRUD service for Snipe-IT manufacturers"""

from proxmox_soc.snipe_it.snipe_api.services.crudbase import CrudBaseService

class ManufacturerService(CrudBaseService):
    """Service for managing asset manufacturers"""
    
    def __init__(self):
        super().__init__('/api/v1/manufacturers', 'manufacturer')