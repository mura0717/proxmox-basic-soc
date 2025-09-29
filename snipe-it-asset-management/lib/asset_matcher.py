"""
Centralized Asset Matching Service
Consolidates data from multiple sources and syncs with Snipe-IT
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from crud.base import BaseCRUDService
from crud.status_labels import StatusLabelService
from crud.categories import CategoryService
from crud.manufacturers import ManufacturerService
from crud.models import ModelService

class AssetService(BaseCRUDService):
    """Service for managing assets"""
    
    def __init__(self):
        super().__init__('/api/v1/hardware', 'asset')
    
    def search_by_serial(self, serial: str) -> Optional[Dict]:
        """Search for asset by serial number"""
        from snipe_api.api_client import make_api_request
        response = make_api_request("GET", f"{self.endpoint}/byserial/{serial}")
        if response and response.json().get("rows"):
            return response.json()["rows"][0]
        return None
    
    def search_by_asset_tag(self, asset_tag: str) -> Optional[Dict]:
        """Search for asset by asset tag"""
        from snipe_api.api_client import make_api_request
        response = make_api_request("GET", f"{self.endpoint}/bytag/{asset_tag}")
        if response and response.json().get("id"):
            return response.json()
        return None

class AssetMatcher:
    """
    Central service for matching and consolidating asset data from multiple sources
    """
    
    def __init__(self):
        self.asset_service = AssetService()
        self.matched_assets = {}
        self.status_service = StatusLabelService()
        self.category_service = CategoryService()
        self.manufacturer_service = ManufacturerService()
        self.model_service = ModelService()
        self.match_rules = self._initialize_match_rules()
        
    def _initialize_match_rules(self) -> Dict:
        """Define matching rules for different data sources"""
        return {
            'primary': ['serial', 'intune_device_id', 'azure_ad_id'],
            'secondary': ['mac_addresses', 'imei', 'asset_tag'],
            'tertiary': ['name', 'primary_user_upn']
        }
    
    def generate_asset_hash(self, identifiers: Dict) -> str:
        """Generate unique hash for asset identification"""
        hash_string = json.dumps(identifiers, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def find_existing_asset(self, asset_data: Dict) -> Optional[Dict]:
        """
        Find existing asset in Snipe-IT using multiple matching strategies
        """
        
        print(f"Looking for existing asset: {asset_data.get('name', 'Unknown')}")
        
        # Try primary identifiers first
        for identifier in self.match_rules['primary']:
            if identifier in asset_data and asset_data[identifier]:
                if identifier == 'serial':
                    existing = self.asset_service.search_by_serial(asset_data[identifier])
                    if existing:
                        print(f"Found existing asset by serial: {existing.get('id')}")
                        return existing
        
        # Try secondary identifiers
        for identifier in self.match_rules['secondary']:
            if identifier in asset_data and asset_data[identifier]:
                if identifier == 'asset_tag':
                    existing = self.asset_service.search_by_asset_tag(asset_data[identifier])
                    if existing:
                        print(f"Found existing asset by asset_tag: {existing.get('id')}")
                        return existing
        
        # Search through all assets for other matches
        all_assets = self.asset_service.get_all()
        for asset in all_assets:
            if self._matches_asset(asset, asset_data):
                return asset
        
        print("No existing asset found")
        return None
    
    def _matches_asset(self, existing_asset: Dict, new_data: Dict) -> bool:
        """Check if existing asset matches new data"""
        # Check custom fields for matches
        for identifier in self.match_rules['primary'] + self.match_rules['secondary']:
            existing_value = existing_asset.get('custom_fields', {}).get(identifier, {}).get('value')
            new_value = new_data.get(identifier)
            
            if existing_value and new_value and existing_value == new_value:
                return True
        
        return False
    
    def merge_asset_data(self, *data_sources: Dict) -> Dict:
        """
        Merge data from multiple sources with priority handling
        Priority: Intune > SNMP > Nmap > Existing
        """
        merged = {}
        
        # Source priorities for conflict resolution - higher number = higher priority
        source_priority = {
            'intune': 4,
            'snmp': 3,
            'nmap': 2,
            'existing': 1
        }
        
        for source_data in data_sources:
            source = source_data.get('_source', 'unknown')
            source_data = {k: v for k, v in source_data.items() if not k.startswith('_')}
            
            for key, value in source_data.items():
                if value is None or value == '':
                    continue
                
                if key not in merged:
                    merged[key] = value
                    merged[f'{key}_source'] = source
                else:
                    # Check if new source has higher priority
                    current_source = merged.get(f'{key}_source', 'unknown')
                    if source_priority.get(source, 0) > source_priority.get(current_source, 0):
                        merged[key] = value
                        merged[f'{key}_source'] = source
        
        # Update metadata
        merged['last_update_source'] = source
        merged['last_update_at'] = datetime.now(timezone.utc).isoformat()
        
        return merged
    
    def process_scan_data(self, scan_type: str, scan_data: List[Dict]) -> Dict:
        """
        Process scan data from various sources
        
        Args:
            scan_type: Type of scan (nmap, snmp, intune, etc.)
            scan_data: List of discovered assets
        
        Returns:
            Dictionary with processing results
        """
        results = {
            'created': 0,
            'updated': 0,
            'failed': 0,
            'assets': []
        }
        
        for asset_data in scan_data:
            asset_data['_source'] = scan_type
            
            # Find existing asset
            existing = self.find_existing_asset(asset_data)
            
            if existing:
                # Merge with existing data
                merged_data = self.merge_asset_data(
                    {'_source': 'existing', **existing},
                    asset_data
                )
                
                # Update asset
                if self._update_asset(existing['id'], merged_data):
                    results['updated'] += 1
                    results['assets'].append({
                        'id': existing['id'],
                        'action': 'updated',
                        'name': merged_data.get('name', 'Unknown')
                    })
                else:
                    results['failed'] += 1
            else:
                # Create new asset
                new_asset = self._create_asset(asset_data)
                if new_asset:
                    results['created'] += 1
                    results['assets'].append({
                        'id': new_asset.get('id'),
                        'action': 'created',
                        'name': asset_data.get('name', 'Unknown')
                    })
                else:
                    results['failed'] += 1
        
        return results
    
    def _create_asset(self, asset_data: Dict) -> Optional[Dict]:
        """Create new asset in Snipe-IT"""
        # Prepare asset data for creation
        payload = self._prepare_asset_payload(asset_data)
        print(f"Creating new asset: {asset_data.get('name', 'Unknown')}")
        # Create asset
        return self.asset_service.create(payload)
    
    def _update_asset(self, asset_id: int, asset_data: Dict) -> bool:
        """Update existing asset in Snipe-IT"""
        # Prepare update payload
        payload = self._prepare_asset_payload(asset_data, is_update=True)
        
        # Update asset
        result = self.asset_service.update(asset_id, payload)
        return result is not None
    
    def _prepare_asset_payload(self, asset_data: Dict, is_update: bool = False) -> Dict:
        """Prepare asset data for Snipe-IT API"""
        
        payload = {}
        debug = os.getenv('ASSET_DEBUG', '0') == '1'  # Add debug flag
        
        # 1. MANUFACTURER & MODEL FIRST (they depend on each other)
        manufacturer_name = asset_data.get('manufacturer', '').strip()
        model_name = asset_data.get('model', '').strip()
        
        # Only process if we have actual data
        if manufacturer_name and model_name:
            # Get or create manufacturer
            manufacturer = self.manufacturer_service.get_by_name(manufacturer_name)
            if not manufacturer:
                manufacturer = self.manufacturer_service.create({
                    'name': manufacturer_name
                })
                if debug:
                    print(f"Created manufacturer: {manufacturer_name}")
            
            if manufacturer:
                payload['manufacturer_id'] = manufacturer['id']
                
                # Determine category
                category_name = self._determine_category(asset_data)
                category = self.category_service.get_by_name(category_name)
                
                if category:
                    payload['category_id'] = category['id']
                    
                    # Create FULL model name (e.g., "LENOVO 20L8002WMD")
                    full_model_name = f"{manufacturer_name} {model_name}"
                    
                    # Check if model exists
                    existing_model = self.model_service.get_by_name(full_model_name)
                    
                    if not existing_model:
                        # Create model with proper fieldset
                        from crud.fieldsets import FieldsetService
                        fieldset_service = FieldsetService()
                        
                        fieldset_map = {
                            'Laptops': 'Managed Assets (Intune+Nmap)',
                            'Desktops': 'Managed Assets (Intune+Nmap)',
                            'Mobile Phones': 'Mobile Devices',
                            'Tablets': 'Mobile Devices',
                            'IoT Devices': 'Managed Assets (Intune+Nmap)',
                        }
                        
                        fieldset_name = fieldset_map.get(category_name, 'Managed Assets (Intune+Nmap)')
                        fieldset = fieldset_service.get_by_name(fieldset_name)
                        
                        model_data = {
                            'name': full_model_name,
                            'manufacturer_id': manufacturer['id'],
                            'category_id': category['id'],
                            'model_number': model_name
                        }
                        
                        if fieldset:
                            model_data['fieldset_id'] = fieldset['id']
                        
                        existing_model = self.model_service.create(model_data)
                        if debug:
                            print(f"Created model: {full_model_name}")
                    
                    if existing_model:
                        payload['model_id'] = existing_model['id']
        
        # 2. FALLBACK to generic if no specific model
        if 'model_id' not in payload:
            device_type = asset_data.get('device_type', '').lower()
            generic_name = self._determine_model_name(device_type)
            generic_model = self.model_service.get_by_name(generic_name)
            
            if generic_model:
                payload['model_id'] = generic_model['id']
                # Set category from generic model if not already set
                if 'category_id' not in payload and generic_model.get('category'):
                    payload['category_id'] = generic_model['category']['id']
        
        # 3. STANDARD FIELDS (only process once)
        standard_fields = ['name', 'asset_tag', 'serial', 'notes']
        for field in standard_fields:
            if field in asset_data and asset_data[field]:
                payload[field] = asset_data[field]
        
        # 4. MAC ADDRESS (built-in field)
        if 'mac_addresses' in asset_data and asset_data['mac_addresses']:
            macs = asset_data['mac_addresses']
            if isinstance(macs, str):
                # Take first MAC for built-in field
                first_mac = macs.split('\n')[0] if '\n' in macs else macs
                if first_mac:
                    payload['mac_address'] = first_mac.strip()
        
        # 5. AUTO-GENERATE ASSET TAG
        if not is_update and 'asset_tag' not in payload:
            payload['asset_tag'] = self._generate_asset_tag(asset_data)
        
        # 6. STATUS
        if 'status_id' not in payload:
            source = asset_data.get('_source', 'unknown')
            status_map = {
                'intune': 'Managed (Intune)',
                'nmap': 'Discovered (Nmap)',
                'snmp': 'On-Premise',
            }
            status_name = status_map.get(source, 'Unknown')
            status = self.status_service.get_by_name(status_name)
            if status:
                payload['status_id'] = status['id']
        
        # 7. CUSTOM FIELDS (corrected format)
        from snipe_api.schema import CUSTOM_FIELDS
        
        for field_key, field_def in CUSTOM_FIELDS.items():
            if field_key in asset_data and asset_data[field_key] is not None:
                field_name = field_def['name']
                value = asset_data[field_key]
                
                # Skip empty values
                if value == "" or value == "Unknown":
                    continue
                
                # Convert based on type
                if field_def['element'] == 'checkbox':
                    value = 1 if value else 0
                elif field_def['element'] == 'textarea' and isinstance(value, (dict, list)):
                    value = json.dumps(value)
                
                # Use exact field name from schema
                payload[field_name] = value
        
        if debug:
            print(f"Final payload for {asset_data.get('name')}:")
            print(f"  Model: {payload.get('model_id')}")
            print(f"  Category: {payload.get('category_id')}")
            print(f"  Status: {payload.get('status_id')}")
        
        return payload
    
    def _generate_asset_tag(self, asset_data: Dict) -> str:
        """Generate unique asset tag"""
        # Use timestamp and partial hash for uniqueness
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        hash_part = self.generate_asset_hash(asset_data)[:6].upper()
        return f"AUTO-{timestamp}-{hash_part}"
    
    def _determine_category(self, asset_data: Dict) -> str:
        """Determine asset category based on data"""
        device_type = asset_data.get('device_type', '').lower()
        os_platform = asset_data.get('os_platform', '').lower()
        manufacturer = asset_data.get('manufacturer', '').lower()
        model = asset_data.get('model', '').lower()
        
        # Category mapping logic
        if (manufacturer == 'yealink' and 
            any(x in model.lower() for x in ['roompanel', 'meetingbar', 'ctp'])):
            return 'Meeting Room Devices'
        
        if 'iot' or 'iot device' in device_type:
            return 'IoT Devices'
        elif 'server' in device_type or 'server' in os_platform:
            return 'Servers'
        elif 'switch' in device_type or 'router' in device_type:
            return 'Network Devices'
        elif 'printer' in device_type:
            return 'Printers'
        elif 'laptop' in device_type:
            return 'Laptops'
        elif 'desktop' in device_type or 'workstation' in device_type:
            return 'Desktops'
        elif 'tablet' in device_type or 'ipad' in os_platform:
            return 'Tablets'
        elif 'phone' in device_type or 'mobile' in device_type:
            return 'Mobile Phones'
        elif 'vm' in device_type or 'virtual' in device_type:
            return 'Virtual Machines (On-Premises)'
        elif asset_data.get('cloud_provider'):
            return 'Cloud Resources'
        else:
            return 'Other Assets'
    
    def _determine_model_name(self, device_type: str) -> str:
        """Determine model name based on device type"""
        device_type = device_type.lower()
        
        model_map = {
            'server': 'Generic Server',
            'desktop': 'Generic Desktop', 
            'laptop': 'Generic Laptop',
            'switch': 'Generic Network Device',
            'router': 'Generic Network Device',
            'printer': 'Generic Printer',
            'mobile phone': 'Generic Mobile Phone',
            'tablet': 'Generic Mobile Phone',
            'virtual machine': 'Generic Virtual Machine',
            'cloud resource': 'Generic Cloud Resource'
        }
        
        for key, model_name in model_map.items():
            if key in device_type:
                return model_name
        
        return 'Generic Unknown Device'