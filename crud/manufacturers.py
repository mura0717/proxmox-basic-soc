#!/usr/bin/env python3

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crud.base import BaseCRUDService

class ManufacturerService(BaseCRUDService):
    """Service for managing asset manufacturers"""
    
    def __init__(self):
        super().__init__('/api/v1/manufacturers', 'manufacturer')