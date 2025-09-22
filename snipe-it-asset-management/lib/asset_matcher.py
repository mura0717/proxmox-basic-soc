"""
Centralized Asset Matching Service
Consolidates data from multiple sources and syncs with Snipe-IT
"""

import hashlib
import json
from datetime import datetime
from typing import Dict, List, Optional
from crud.base import BaseCRUDService

class AssetService(BaseCRUDService):
    """Service for managing assets"""
    
    def __init__(self):
        super().__init__('/api/v1/hardware', 'asset')
    
    def search_by_serial(self, serial: str) -> Optional[Dict]:
        """Search for asset by serial number"""
        from ..snipe_api.api_client import make_api_request
        response = make_api_request("GET", f"{self.endpoint}/byserial/{serial}")
        if response and response.json().get("rows"):
            return response.json()["rows"][0]
        return None
    
    def search_by_asset_tag(self, asset_tag: str) -> Optional[Dict]:
        """Search for asset by asset tag"""
        from ..snipe_api.api_client import make_api_request
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
        self.match_rules = self._initialize_match_rules()
    
    def _initialize_match_rules(self) -> Dict:
        """Define matching rules for different data sources"""
        return {
            'primary': ['serial_number', 'intune_device_id', 'azure_ad_id'],
            'secondary': ['mac_addresses', 'imei', 'asset_tag'],
            'tertiary': ['dns_hostname', 'primary_user_upn']
        }
    
    def generate_asset_hash(self, identifiers: Dict) -> str:
        """Generate unique hash for asset identification"""
        hash_string = json.dumps(identifiers, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def find_existing_asset(self, asset_data: Dict) -> Optional[Dict]:
        """
        Find existing asset in Snipe-IT using multiple matching strategies
        """
        # Try primary identifiers first
        for identifier in self.match_rules['primary']:
            if identifier in asset_data and asset_data[identifier]:
                if identifier == 'serial_number':
                    existing = self.asset_service.search_by_serial(asset_data[identifier])
                    if existing:
                        return existing
        
        # Try secondary identifiers
        for identifier in self.match_rules['secondary']:
            if identifier in asset_data and asset_data[identifier]:
                if identifier == 'asset_tag':
                    existing = self.asset_service.search_by_asset_tag(asset_data[identifier])
                    if existing:
                        return existing
        
        # Search through all assets for other matches
        all_assets = self.asset_service.get_all()
        for asset in all_assets:
            if self._matches_asset(asset, asset_data):
                return asset
        
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
        
        # Define source priorities
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
        merged['last_update_at'] = datetime.utcnow().isoformat()
        
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
        from crud.status_labels import StatusLabelService
        from crud.categories import CategoryService
        
        # Get service instances
        status_service = StatusLabelService()
        category_service = CategoryService()
        
        # Base payload
        payload = {}
        
        # Standard fields
        standard_fields = ['name', 'asset_tag', 'serial', 'model_id', 'status_id', 
                          'category_id', 'manufacturer_id', 'location_id', 'notes']
        
        for field in standard_fields:
            if field in asset_data:
                payload[field] = asset_data[field]
        
        # Auto-generate asset tag if not provided
        if not is_update and 'asset_tag' not in payload:
            payload['asset_tag'] = self._generate_asset_tag(asset_data)
        
        # Set status based on source
        if 'status_id' not in payload:
            source = asset_data.get('_source', 'unknown')
            status_map = {
                'intune': 'Managed (Intune)',
                'nmap': 'Discovered (Nmap)',
                'snmp': 'On-Premise',
                'azure': 'Cloud Resource'
            }
            status_name = status_map.get(source, 'Unknown')
            status = status_service.get_by_name(status_name)
            if status:
                payload['status_id'] = status['id']
        
        # Determine category
        if 'category_id' not in payload:
            category_name = self._determine_category(asset_data)
            category = category_service.get_by_name(category_name)
            if category:
                payload['category_id'] = category['id']
        
        # Custom fields
        custom_fields = {}
        from ..snipe_api.schema import CUSTOM_FIELDS
        
        for field_key, field_def in CUSTOM_FIELDS.items():
            field_name = field_def['name']
            if field_key in asset_data:
                # Convert value based on field type
                value = asset_data[field_key]
                if field_def['element'] == 'checkbox':
                    value = 1 if value else 0
                elif field_def['element'] == 'textarea' and isinstance(value, (dict, list)):
                    value = json.dumps(value)
                
                custom_fields[field_name] = value
        
        if custom_fields:
            payload.update(custom_fields)
        
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
        
        # Category mapping logic
        if 'server' in device_type or 'server' in os_platform:
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