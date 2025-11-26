#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.services.crudbase import BaseCRUDService

class ModelService(BaseCRUDService):
    """Service for managing asset models"""
    
    def __init__(self):
        super().__init__('/api/v1/models', 'model')
        
    
