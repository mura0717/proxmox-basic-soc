"""CRUD service for Snipe-IT status labels"""

from base import BaseCRUDService

class StatusLabelService(BaseCRUDService):
    """Service for managing status labels"""
    
    def __init__(self):
        super().__init__('/api/v1/statuslabels', 'status label')