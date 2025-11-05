"""CRUD service for Snipe-IT custom fields"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crud.base import BaseCRUDService
from snipe_api.api_client import make_api_request

class FieldService(BaseCRUDService):
    """Service for managing custom fields"""
    
    def __init__(self):
        super().__init__('/api/v1/fields', 'field')
    
    def associate_to_fieldset(self, field_id: int, fieldset_id: int) -> bool:
        """Associate field with fieldset"""
        
        payload = {"fieldset_id": fieldset_id}
        response = make_api_request(
            "POST",
            f"{self.endpoint}/{field_id}/associate",
            json=payload
        )
        
        if response and response.ok:
            return True
        elif response and response.status_code in (409, 422):
            # Already associated
            return True
        return False
    
    def disassociate_from_fieldset(self, field_id: int, fieldset_id: int) -> bool:
        """Disassociate field from fieldset"""
        
        response = make_api_request(
            "POST",
            f"{self.endpoint}/{field_id}/disassociate",
            json={"fieldset_id": fieldset_id}
        )
        return response and response.ok