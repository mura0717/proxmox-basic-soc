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
from crud.status_labels import StatusLabelService
from crud.categories import CategoryService
from crud.manufacturers import ManufacturerService
from crud.models import ModelService
from crud.assets import AssetService
from crud.locations import LocationService
from assets_sync_library.asset_categorizer import AssetCategorizer
from assets_sync_library.asset_finder import AssetFinder
from config.snipe_schema import CUSTOM_FIELDS
from config.network_config import STATIC_IP_MAP
from assets_sync_library.mac_utils import normalize_mac

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
        self.location_service = LocationService()
        self.finder = AssetFinder(self.asset_service) # Instantiate finder once
        self.debug = os.getenv('ASSET_MATCHER_DEBUG', '0') == '1'
    
    def generate_asset_hash(self, identifiers: Dict) -> str:
        """Generate unique hash for asset identification"""
        hash_string = json.dumps(identifiers, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()
    
    # --- Public Methods ---
    
    def clear_all_caches(self):
        """Clears the internal caches of all services to ensure fresh data."""
        print("Clearing all local service caches...")
        self.asset_service._cache.clear()
        self.status_service._cache.clear()
        self.category_service._cache.clear()
        self.manufacturer_service._cache.clear()
        self.model_service._cache.clear()
        self.finder._all_assets_cache = None # Clear finder's asset cache
    
    def process_scan_data(self, scan_type: str, scan_data: List[Dict]) -> Dict:
        """
        Process scan data from various sources.
        This is the main entry point for the class.
        Args:
            scan_type: Type of scan (nmap, snmp, intune, etc.)
            scan_data: List of discovered assets
        Returns:
            Dictionary with processing results
        """
        results = self._initialize_results()
        return self._process_assets(scan_type, scan_data, results)
    
    def find_existing_asset(self, asset_data: Dict) -> Optional[Dict]:
        """
        Find an existing asset in Snipe-IT using a prioritized chain of matching strategies.
        """
        print(f"Looking for existing asset: {asset_data.get('name', 'Unknown')}")

        # The order of these calls defines the matching priority.
        found_asset = ( # Use the class-level finder instance
            self.finder.by_serial(asset_data.get('serial')) or
            self.finder.by_asset_tag(asset_data.get('asset_tag')) or
            self.finder.by_static_mapping(asset_data.get('last_seen_ip')) or
            self.finder.by_mac_address(asset_data) or
            self.finder.by_hostname(asset_data) or
            self.finder.by_ip_address(asset_data.get('last_seen_ip')) or
            self.finder.by_fallback_identifiers(asset_data)
        )

        if found_asset:
            return found_asset
            
        print("No existing asset found")
        return None

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

    # --- Private Orchestration Methods ---

    def _process_assets(self, scan_type: str, scan_data: List[Dict], results: Dict) -> Dict:
        """Iterate through scan data and process each asset."""
        for asset_data in scan_data:
            asset_data['_source'] = scan_type

            # --- Static IP Override (Highest Priority) ---
            # Apply static mapping data at the very beginning to enrich the incoming data.
            ip_address = asset_data.get('last_seen_ip')
            if ip_address and ip_address in STATIC_IP_MAP:
                asset_data.update(STATIC_IP_MAP[ip_address])
            
            existing = self.find_existing_asset(asset_data)
            
            if existing:
                # Merge with existing data and update
                merged_data = self.merge_asset_data({'_source': 'existing', **existing}, asset_data)
                if self._update_asset(existing['id'], merged_data):
                    results['updated'] += 1
                    results['assets'].append({'id': existing['id'], 'action': 'updated', 'name': merged_data.get('name', 'Unknown')})
                else:
                    results['failed'] += 1
            else:
                # Create new asset if it has sufficient data
                if self._has_sufficient_data(asset_data):
                    new_asset = self._create_asset(asset_data)
                    if new_asset:
                        results['created'] += 1
                        results['assets'].append({'id': new_asset.get('id'), 'action': 'created', 'name': asset_data.get('name', 'Unknown')})
                    else:
                        results['failed'] += 1
                else:
                    results['skipped_insufficient_data'] += 1
                    print(f"  ⊘ Insufficient data to create: {asset_data.get('name')} (need MAC, serial, or unique hostname/ID)")
        
        return results

    def _create_asset(self, asset_data: Dict) -> Optional[Dict]:
        """Prepare and create a new asset in Snipe-IT."""
        payload = self._prepare_asset_payload(asset_data)
        print(f"Creating new asset: {asset_data.get('name', 'Unknown')}")
        return self.asset_service.create(payload)
    
    def _update_asset(self, asset_id: int, asset_data: Dict) -> bool:
        """Prepare and update an existing asset in Snipe-IT."""
        payload = self._prepare_asset_payload(asset_data, is_update=True)
        result = self.asset_service.update(asset_id, payload)
        return result is not None

    def _prepare_asset_payload(self, asset_data: Dict, is_update: bool = False) -> Dict:
        """Orchestrate the preparation of the asset data payload for the Snipe-IT API."""
        payload = {}

        # --- Step 1: Set the definitive asset name (Highest Priority) ---
        # Use the trusted hostname from the static map if it exists. This must happen first.
        if asset_data.get('host_name'):
            asset_data['name'] = asset_data['host_name']

        self._handle_model_and_category(payload, asset_data)
        self._populate_standard_fields(payload, asset_data, is_update)
        self._populate_custom_fields(payload, asset_data)
        return payload
    
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
        if asset_data.get('azure_ad_id'):
            return True
        dns_hostname = asset_data.get('dns_hostname', '') # Real not generic
        if dns_hostname and not dns_hostname.startswith('Device-') and dns_hostname not in ['', '_gateway']:
            return True
        return False
    
    # --- Private Helper Methods ---

    def _handle_model_and_category(self, payload: Dict, asset_data: Dict):
        """Determine and assign manufacturer, model, and category."""
        manufacturer_name = str(asset_data.get('manufacturer') or '').strip()
        model_name = str(asset_data.get('model') or '').strip()
        
        # Only process if we have actual data
        if manufacturer_name and model_name:
            # Use "get or create" logic to prevent errors for existing manufacturers
            manufacturer = self.manufacturer_service.get_or_create({'name': manufacturer_name})
    
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
                            
                        if self.debug:
                            print(f"[DEBUG] Model '{full_model_name}' not found. Attempting to create...")
                            print(f"[DEBUG] Model creation payload: {json.dumps(model_data, indent=2)}")
                        
                        newly_created_model = self.model_service.create(model_data)
                        
                        if newly_created_model:
                            # It was created successfully!
                            existing_model = newly_created_model
                            if self.debug:
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
                        if category and (not existing_model.get('category') or existing_model.get('category', {}).get('id') != category['id']):
                            if self.debug:
                                old_cat = (existing_model.get('category') or {}).get('name')
                                print(f"[DEBUG] Updating model category: {existing_model.get('name')} from {old_cat} to {category['name']}")
                            self.model_service.update(existing_model['id'], {'category_id': category['id']})
                            self.model_service.get_all(refresh_cache=True)
        
        # 2. FALLBACK to generic if no specific model
        if 'model_id' not in payload:
            self._assign_generic_model(payload, asset_data)

    def _assign_generic_model(self, payload: Dict, asset_data: Dict):
        if 'model_id' not in payload:
            device_type = str(asset_data.get('device_type') or '').lower()
            generic_model_name = self._determine_model_name(device_type)
            generic_model_obj = self.model_service.get_by_name(generic_model_name)
            
            if self.debug:
                print(f"[DEBUG] No specific model found. Looking for generic: '{generic_model_name}'")
        
            if generic_model_obj:
                payload['model_id'] = generic_model_obj['id']
                # Set category from generic model if not already set
                if 'category_id' not in payload and generic_model_obj.get('category'):
                    payload['category_id'] = generic_model_obj['category']['id']    
                if self.debug:
                    print(f"[DEBUG] Successfully found and assigned generic model ID: {payload['model_id']}")
            else:
                raise ValueError(
                    f"FATAL: The required generic model '{generic_model_name}' was not found in Snipe-IT. "
                    f"Please ensure the initialization script has been run and the model exists."
                )

    def _populate_standard_fields(self, payload: Dict, asset_data: Dict, is_update: bool):
        """Populate standard, non-custom fields in the payload."""
        # 1. Basic text fields
        standard_fields = ['name', 'asset_tag', 'serial', 'notes']
        for field in standard_fields:
            if field in asset_data and asset_data[field]:
                payload[field] = asset_data[field]
        
        # 2. MAC ADDRESS (built-in field)
        if 'mac_addresses' in asset_data and asset_data['mac_addresses']:
            macs = asset_data['mac_addresses']
            if isinstance(macs, str):
                # Take first MAC for built-in field
                first_mac = macs.split('\n')[0] if '\n' in macs else macs
                if first_mac:
                    payload['mac_address'] = normalize_mac(first_mac.strip())
        
        # 3. AUTO-GENERATE ASSET TAG for new assets
        if not is_update and 'asset_tag' not in payload:
            payload['asset_tag'] = self._generate_asset_tag(asset_data)
       
        # 4. LOCATION
        location_name = asset_data.get('location')
        if location_name:
            # Ensure location_name is a string, not a dictionary
            if isinstance(location_name, dict):
                location_name = location_name.get('name')

            location = self.location_service.get_by_name(location_name)
            if not location:
                print(f"  -> Location '{location_name}' not found. Creating it now...")
                location = self.location_service.create({'name': location_name})

            if location and location.get('id'):
                payload['location_id'] = location['id']
            else:
                print(f"  [ERROR] Failed to find or create location '{location_name}'. Asset will have no location.")
        
        # 5. STATUS
        self._determine_status(payload, asset_data)
        
        

    def _populate_custom_fields(self, payload: Dict, asset_data: Dict):
        """Populate all custom fields in the payload."""
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

    def _determine_status(self, payload: Dict, asset_data: Dict):
        """Determines and sets the status_id for the asset."""
        if 'status_id' in payload:
            return

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

    def _initialize_results(self) -> Dict:
        """Returns a clean dictionary for tracking sync results."""
        return {'created': 0, 'updated': 0, 'failed': 0, 'skipped_insufficient_data': 0, 'assets': []}

    def _determine_category(self, asset_data: Dict) -> str:
        """Determine asset category based on data by calling the AssetCategorizer."""
        classification = AssetCategorizer.categorize(asset_data)
        asset_data.update(classification) # Ensure device_type is available for model determination
        if self.debug:
            print(f"Categorization for {asset_data.get('name')}: {classification}")
        return classification.get('category', 'Other Assets')
    
    def _generate_asset_tag(self, asset_data: Dict) -> str:
        """Generate unique asset tag"""
        # Use timestamp and partial hash for uniqueness
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        hash_part = self.generate_asset_hash(asset_data)[:6].upper()
        return f"AUTO-{timestamp}-{hash_part}"
        
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