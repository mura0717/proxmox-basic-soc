"""CRUD service for Snipe-IT status labels"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.services.crudbase import BaseCRUDService

class StatusLabelService(BaseCRUDService):
    """Service for managing status labels"""
    
    def __init__(self):
        super().__init__('/api/v1/statuslabels', 'status label')