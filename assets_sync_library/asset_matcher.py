"""
Centralized Asset Matching Service
Consolidates data from multiple sources and syncs with Snipe-IT
"""

import os
import sys
import hashlib
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from crud.base import BaseCRUDService
from crud.status_labels import StatusLabelService
from crud.categories import CategoryService
from crud.manufacturers import ManufacturerService
from crud.models import ModelService
from snipe_api.schema import CUSTOM_FIELDS
from assets_sync_library.asset_categorizer import AssetCategorizer
from crud.assets import AssetService
from assets_sync_library.mac_utils import (
    macs_from_keys, macs_from_any, intersect_mac_sets, normalize_mac
) 

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
        
    def clear_all_caches(self):
        """Clears the internal caches of all services to ensure fresh data."""
        print("Clearing all local service caches...")
        self.asset_service._cache.clear()
        self.status_service._cache.clear()
        self.category_service._cache.clear()
        self.manufacturer_service._cache.clear()
        self.model_service._cache.clear()    
        
    def _initialize_match_rules(self) -> Dict:
        """Define matching rules for different data sources with clear priorities"""
        return {
            'exact': ['serial', 'intune_device_id', 'azure_ad_id'],
            'hardware': ['mac_addresses'],
            'administrative': ['asset_tag'], 
            'network': ['dns_hostname', 'last_seen_ip']
        }
    
    def _get_custom_field(self, existing_asset: Dict, key: str) -> Optional[str]:
        field_def = CUSTOM_FIELDS.get(key)
        if not field_def:
            return None
        label = field_def['name']
        return (existing_asset.get('custom_fields', {})
                            .get(label, {})
                            .get('value')) 
    
    def generate_asset_hash(self, identifiers: Dict) -> str:
        """Generate unique hash for asset identification"""
        hash_string = json.dumps(identifiers, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    def _ensure_all_assets_fetched(self, all_assets: Optional[List[Dict]]) -> List[Dict]:
        """Lazily fetches all assets from the API, only if the list is not already populated."""
        if all_assets is None:
            print("  -> Lazily fetching all assets for deep matching...")
            return self.asset_service.get_all()
        return all_assets

    def find_existing_asset(self, asset_data: Dict) -> Optional[Dict]:
        """
        Find existing asset in Snipe-IT using multiple matching strategies
        """
    
        print(f"Looking for existing asset: {asset_data.get('name', 'Unknown')}")
        all_assets = None
        
        # STRATEGY 1: Fast API searches
        # Serial search
        if asset_data.get('serial'):
            existing = self.asset_service.search_by_serial(asset_data['serial'])
            if existing:
                print(f"  ✓ Found by serial: {asset_data['serial']} (ID: {existing.get('id')})")
                return existing
        
        # Asset tag search  
        if asset_data.get('asset_tag'):
            existing = self.asset_service.search_by_asset_tag(asset_data['asset_tag'])
            if existing:
                print(f"  ✓ Found by asset_tag: {asset_data['asset_tag']} (ID: {existing.get('id')})")
                return existing
        
        # STRATEGY 2: MAC Address searches
        MAC_FIELDS = ('mac_addresses', 'wifi_mac', 'ethernet_mac', 'mac_address')        
        new_macs = macs_from_keys(asset_data, MAC_FIELDS)

        if new_macs:
            all_assets = self._ensure_all_assets_fetched(all_assets)
            for asset in all_assets:
                # Built-in MAC
                existing_set = macs_from_any(asset.get('mac_address'))
                # Custom field MACs (schema-aware)
                custom = self._get_custom_field(asset, 'mac_addresses')
                existing_set |= macs_from_any(custom)

                hit = intersect_mac_sets(new_macs, existing_set)
                if hit:
                    print(f"  ✓ Found by MAC: {hit} (ID: {asset.get('id')})")
                    return asset

        # STRATEGY 3: Hostname searches
        dns_hostname = asset_data.get('dns_hostname') or asset_data.get('name')
        if isinstance(dns_hostname, str) and not dns_hostname.startswith('Device-'):
            all_assets = self._ensure_all_assets_fetched(all_assets)
            clean = dns_hostname.split('.')[0].lower()
            for asset in all_assets:
                name = asset.get('name')
                if isinstance(name, str) and clean == name.split('.')[0].lower():
                    print(f"  ✓ Found by hostname: '{dns_hostname}' → '{name}' (ID: {asset.get('id')})")
                    return asset
                cf_host = self._get_custom_field(asset, 'dns_hostname')
                if isinstance(cf_host, str) and clean == cf_host.split('.')[0].lower():
                    print(f"  ✓ Found by DNS hostname: {dns_hostname} (ID: {asset.get('id')})")
                    return asset

        # STRATEGY 4: IP searches
        if asset_data.get('last_seen_ip'):
            all_assets = self._ensure_all_assets_fetched(all_assets)
            for asset in all_assets:
                if self._get_custom_field(asset, 'last_seen_ip') == asset_data['last_seen_ip']:
                    print(f"  ✓ Found by IP: {asset_data['last_seen_ip']} (ID: {asset.get('id')})")
                    return asset

        # STRATEGY 5: Fallback custom fields
        all_assets = self._ensure_all_assets_fetched(all_assets)
        for asset in all_assets:
            if self._matches_asset(asset, asset_data):
                print(f"  ✓ Found by custom field match (ID: {asset.get('id')})")
                return asset

        print("No existing asset found")
        return None
    
    def _matches_asset(self, existing_asset: Dict, new_data: Dict) -> bool:
        for identifier in (self.match_rules['exact'] + 
                        self.match_rules['hardware'] + 
                        self.match_rules['administrative']):
            if identifier == 'mac_addresses':
                continue
            existing_value = self._get_custom_field(existing_asset, identifier)
            new_value = new_data.get(identifier)
            if isinstance(existing_value, str) and isinstance(new_value, str):
                if existing_value.strip().lower() == new_value.strip().lower():
                    return True
            elif existing_value == new_value:
                return True
        return False
    
    def merge_asset_data(self, *data_sources: Dict) -> Dict:
        """
        Merge data from multiple sources with priority handling
        Priority: Intune > SNMP > Nmap > Existing
        """
        merged = {}
        highest_priority_source = 'unknown'
        last_event_source = None
        
        # Source priorities for conflict resolution - higher number = higher priority
        source_priority = {
            'intune': 4,
            'nmap': 3,
            'snmp': 2,
            'existing': 1
        }
        
        for source_data in data_sources:
            source = source_data.get('_source', 'unknown')
            last_event_source = source
            
            #_source is passed before removal so will be available in the categorizer whether the asset is being created or updated!
            if source_priority.get(source, 0) > source_priority.get(highest_priority_source, 0):
                highest_priority_source = source
            
            source_data: Dict[str, Any] = {k: v for k, v in source_data.items() if not k.startswith('_')}
            
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
        
        # Preserve the highest priority _source field
        merged['_source'] = highest_priority_source
        
        # Update metadata
        merged['last_update_source'] = last_event_source
        merged['last_update_at'] = datetime.now(timezone.utc).isoformat()
        
        return merged
    
    def _has_sufficient_data(self, asset_data: Dict) -> bool:
        """
        Determine if we have enough data to confidently create a new asset.
        """
        if asset_data.get('serial'):
            return True
        if asset_data.get('mac_addresses') or asset_data.get('wifi_mac') or asset_data.get('ethernet_mac'):
            return True
        if asset_data.get('intune_device_id'):
            return True

        # Real hostname (not generic)
        dns_hostname = asset_data.get('dns_hostname', '')
        if dns_hostname and not dns_hostname.startswith('Device-') and dns_hostname not in ['', '_gateway']:
            return True
        return False
    
    def process_scan_data(self, scan_type: str, scan_data: List[Dict]) -> Dict:
        """
        Process scan data from various sources
        Only creates assets with sufficient identifying data
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
            'skipped_insufficient_data': 0,
            'assets': []
        }
        
        for asset_data in scan_data:
            asset_data['_source'] = scan_type
            
            # Check if we have sufficient data to confidently create an asset
            can_create = self._has_sufficient_data(asset_data)
            
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
                if can_create:
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
                else:
                    # Skip creation - insufficient data
                    results['skipped_insufficient_data'] += 1
                    print(f"  ⊘ Insufficient data to create: {asset_data.get('name')} (need MAC, serial, or services)")
        
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
        debug = os.getenv('ASSET_MATCHER_DEBUG', '0') == '1'
        
        classification = AssetCategorizer.categorize(asset_data)
        
        asset_data['device_type'] = classification.get('device_type')
        asset_data['cloud_provider'] = classification.get('cloud_provider')
        category_name = classification.get('category', 'Other Assets')
        manufacturer_name = str(asset_data.get('manufacturer') or '').strip()
        model_name = str(asset_data.get('model') or '').strip()
        
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
                        
                        # If same, omit model_number - uniqueness constraint
                        if full_model_name == model_name:
                            model_data.pop('model_number', None)
                        
                        if fieldset:
                            model_data['fieldset_id'] = fieldset['id']
                            
                        if debug:
                            print(f"[DEBUG] Model '{full_model_name}' not found. Attempting to create...")
                            print(f"[DEBUG] Model creation payload: {json.dumps(model_data, indent=2)}")
                        
                        newly_created_model = self.model_service.create(model_data)
                        
                        if newly_created_model:
                            # It was created successfully!
                            existing_model = newly_created_model
                            if debug:
                                print(f"Successfully created model: {full_model_name} (ID: {existing_model.get('id')})")
                        else:
                        # It failed to be created. Try to find it one last time in case of a race condition.
                            print(f"[WARNING] Model creation for '{full_model_name}' failed. Retrying lookup...")
                            self.model_service.get_all(refresh_cache=True)
                            existing_model = self.model_service.get_by_name(full_model_name)
                            if not existing_model:
                                print(f"[ERROR] Could not create or find model '{full_model_name}'. Asset will be processed without a specific model.")
                    #  To automatically correct the category of an existing model.
                    if existing_model:
                        payload['model_id'] = existing_model['id']
                        if category and (not existing_model.get('category') or existing_model['category'].get('id') != category['id']):
                            if debug:
                                old_cat = (existing_model.get('category') or {}).get('name')
                                print(f"[DEBUG] Updating model category: {existing_model.get('name')} from {old_cat} to {category['name']}")
                            self.model_service.update(existing_model['id'], {'category_id': category['id']})
                            self.model_service.get_all(refresh_cache=True)
        
        # 2. FALLBACK to generic if no specific model
        if 'model_id' not in payload:
            device_type = str(asset_data.get('device_type') or '').lower()
            generic_model_name = self._determine_model_name(device_type)
            generic_model_obj = self.model_service.get_by_name(generic_model_name)
            
            if debug:
                print(f"[DEBUG] No specific model found. Looking for generic: '{generic_model_name}'")
        
            if generic_model_obj:
                payload['model_id'] = generic_model_obj['id']
                # Set category from generic model if not already set
                if 'category_id' not in payload and generic_model_obj.get('category'):
                    payload['category_id'] = generic_model_obj['category']['id']    
                if debug:
                    print(f"[DEBUG] Successfully found and assigned generic model ID: {payload['model_id']}")
            else:
                raise ValueError(
                    f"FATAL: The required generic model '{generic_model_name}' was not found in Snipe-IT. "
                    f"Please ensure the initialization script has been run and the model exists."
                )
                
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
                    payload['mac_address'] = normalize_mac(first_mac.strip())
        
        # 5. AUTO-GENERATE ASSET TAG
        if not is_update and 'asset_tag' not in payload:
            payload['asset_tag'] = self._generate_asset_tag(asset_data)
        
        # 6. STATUS
        
        status_name = None
        if 'status_id' not in payload:
            source_for_status = (asset_data.get('_source') or asset_data.get('last_update_source') or 'unknown')
            status_map = {
                'intune': 'Managed (Intune)',
                'nmap': 'Discovered (Nmap)',
                'snmp': 'On-Premise',
            }
            status_name = status_map.get(source_for_status, 'Unknown')
            status = self.status_service.get_by_name(status_name)
            if status:
                payload['status_id'] = status['id']
        
        # 7. CUSTOM FIELDS (corrected format)        
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
            print(f"  Model: {model_name}", "with id: " f"{payload.get('model_id')}")
            print(f"  Category: {category_name}", "with id: " f"{payload.get('category_id')}")
            print(f"  Status: {status_name}", "with id: " f"{payload.get('status_id')}")
        
        return payload
    
    def _generate_asset_tag(self, asset_data: Dict) -> str:
        """Generate unique asset tag"""
        # Use timestamp and partial hash for uniqueness
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        hash_part = self.generate_asset_hash(asset_data)[:6].upper()
        return f"AUTO-{timestamp}-{hash_part}"
    
    def _determine_category(self, asset_data: Dict) -> str:
        """Determine asset category based on data"""
        result = AssetCategorizer.categorize(asset_data)
        # DeviceCategorizer.categorize should return {'device_type': ..., 'category': ...}
        if isinstance(result, dict):
            return result.get('category', 'Other Assets')
        # fallback if categorizer returns something else
        return str(result) if result else 'Other Assets'
        
    def _determine_model_name(self, device_type: str) -> str:
        """Determine model name based on device type"""
        device_type = device_type.lower()
        
        model_map = {
            'server': 'Generic Server',
            'desktop': 'Generic Desktop',
            'laptop': 'Generic Laptop',
            'switch': 'Generic Switch',
            'router': 'Generic Router',
            'firewall': 'Generic Firewall',
            'access point': 'Generic Access Point',
            'printer': 'Generic Printer',
            'mobile phone': 'Generic Mobile Phone',
            'tablet': 'Generic Tablet',
            'virtual machine': 'Generic Virtual Machine',
            'storage device': 'Generic Storage Device',
            'software license': 'Generic Software License', 
            'cloud resource': 'Generic Cloud Resource',
            'domain controller': 'Generic Domain Controller',
            'database server': 'Generic Database Server',
            'web server': 'Generic Web Server'
        }
        
        for key, model_name in model_map.items():
            if key in device_type:
                return model_name
        
        return 'Generic Unknown Device'