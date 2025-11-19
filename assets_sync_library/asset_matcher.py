"""
Centralized Asset Matching Service
Consolidates data from multiple sources and syncs with Snipe-IT
"""

import os
import sys
import hashlib
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crud.status_labels import StatusLabelService
from crud.categories import CategoryService
from crud.manufacturers import ManufacturerService
from crud.models import ModelService
from crud.assets import AssetService
from crud.locations import LocationService
from crud.fields import FieldService
from crud.fieldsets import FieldsetService
from assets_sync_library.asset_categorizer import AssetCategorizer
from assets_sync_library.asset_finder import AssetFinder
from config.snipe_schema import CUSTOM_FIELDS, MODELS
from config.network_config import STATIC_IP_MAP
from debug.asset_debug_logger import debug_logger
from utils.mac_utils import normalize_mac
from utils.text_utils import normalize_for_comparison

class AssetMatcher:
    
    _custom_field_map: Dict[str, str] = {}
    _hydrated = False
    
    def __init__(self):
        self.asset_service = AssetService()
        self.matched_assets = {}
        self.status_service = StatusLabelService()
        self.category_service = CategoryService()
        self.manufacturer_service = ManufacturerService()
        self.model_service = ModelService()
        self.location_service = LocationService()
        self.finder = AssetFinder(self.asset_service)
        self.field_service = FieldService()
        self.fieldset_service = FieldsetService()        
        self.debug = os.getenv('ASSET_MATCHER_DEBUG', '0') == '1'
        if not AssetMatcher._hydrated:
            self._hydrate_field_map()
    
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
        if self.debug:
            print(f"Looking for existing asset: {asset_data.get('name', 'Unknown')}")

        # The order of these calls defines the matching priority
        found_asset = (
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
            
        if self.debug:
            print("No existing asset found.")
        return None

    def merge_asset_data(self, *data_sources: Dict) -> Dict:
        """
        Merge data from multiple sources with priority handling
        """
        # Lower number = higher priority. This makes it easier to find the min.
        source_priority = {
            'intune': 1,
            'teams': 2,
            'nmap': 3,
            'snmp': 4,
            'existing': 99
        }

        # Start with the lowest priority data source and layer higher priority ones on top.
        sorted_sources = sorted(data_sources, key=lambda d: source_priority.get(d.get('_source', 'existing'), 99))

        merged = {}
        for source_data in data_sources:
            for key, value in source_data.items():
                # Ignore internal keys
                if key.startswith('_'):
                    continue

                # Add the value if the key doesn't exist yet,
                # OR if the new value is not empty/None.
                # This prevents a high-priority source from blanking out a field.
                if key not in merged or (value is not None and value != ''):
                    merged[key] = value

        return merged

    # --- Private Orchestration Methods ---

    def _process_assets(self, scan_type: str, scan_data: List[Dict], results: Dict) -> Dict:
        """Iterate through scan data and process each asset."""
        for asset_data in scan_data:
            asset_data['_source'] = scan_type

            # Enrich with static IP mapping data first
            ip_address = asset_data.get('last_seen_ip')
            if ip_address and ip_address in STATIC_IP_MAP:
                asset_data.update(STATIC_IP_MAP[ip_address])
            
            existing = self.find_existing_asset(asset_data)
            
            if existing:
                
                flattened_existing = {**existing} # Create a copy
                if isinstance(flattened_existing.get('model'), dict):
                    flattened_existing['model'] = flattened_existing['model'].get('name')
                if isinstance(flattened_existing.get('manufacturer'), dict):
                    flattened_existing['manufacturer'] = flattened_existing['manufacturer'].get('name')
                    
                # Merge with existing data and update
                merged_data = self.merge_asset_data({'_source': 'existing', **flattened_existing}, asset_data)
                # Ensure the source from the new scan is preserved for categorization.
                merged_data['_source'] = scan_type

                if self._update_asset(existing['id'], merged_data, scan_type):
                    results['updated'] += 1
                    results['assets'].append({'id': existing['id'], 'action': 'updated', 'name': merged_data.get('name', 'Unknown')})
                else:
                    results['failed'] += 1
            else:
                # Create new asset if it has sufficient data
                if self._has_sufficient_data(asset_data):
                    new_asset = self._create_asset(asset_data, scan_type)
                    if new_asset:
                        results['created'] += 1
                        results['assets'].append({'id': new_asset.get('id'), 'action': 'created', 'name': asset_data.get('name', 'Unknown')})
                    else:
                        results['failed'] += 1
                else:
                    results['skipped_insufficient_data'] += 1
                    print(f"  ⊘ Insufficient data to create: {asset_data.get('name')} (need MAC, serial, or unique hostname/ID)")
        
        return results

    def _create_asset(self, asset_data: Dict, scan_type: str) -> Optional[Dict]:
        """Prepare and create a new asset in Snipe-IT."""
        payload = self._prepare_asset_payload(asset_data)
        asset_name = asset_data.get('name', 'Unknown')
        
        if debug_logger.is_enabled:
            debug_logger.log_final_payload(scan_type, 'create', asset_name, payload)
            
        print(f"Creating new asset: {asset_name}")
        return self.asset_service.create(payload)
    
    def _update_asset(self, asset_id: int, asset_data: Dict, scan_type: str) -> bool:
        """Prepare and update an existing asset in Snipe-IT."""
        payload = self._prepare_asset_payload(asset_data, is_update=True)
        
        if debug_logger.is_enabled:
            debug_logger.log_final_payload(scan_type, 'update', asset_data.get('name', 'Unknown'), payload)
            
        result = self.asset_service.update(asset_id, payload)
        return result is not None
    
    def _prepare_asset_payload(self, asset_data: Dict, is_update: bool = False) -> Dict:
        """Orchestrate the preparation of the asset data payload for the Snipe-IT API."""
        payload = {}

        # Use trusted hostname from static map as the definitive asset name
        if asset_data.get('host_name'):
            asset_data['name'] = asset_data['host_name']

        self._assign_model_manufacturer_category(payload, asset_data)
        self._populate_standard_fields(payload, asset_data, is_update)
        self._populate_custom_fields(payload, asset_data)
        
        return payload
    
    def _has_sufficient_data(self, asset_data: Dict) -> bool:
        """
        Determine if we have enough data to confidently create a new asset.
        """
        # An IP-only asset will be created but flagged for review.
        if asset_data.get('last_seen_ip') and not (asset_data.get('serial') or asset_data.get('mac_addresses') or asset_data.get('intune_device_id')):
            return True
        if asset_data.get('last_seen_ip') in STATIC_IP_MAP:  # An IP in our trusted static map is sufficient.
            return True
        if asset_data.get('serial'):
            return True
        if asset_data.get('mac_addresses') or asset_data.get('wifi_mac') or asset_data.get('ethernet_mac'):
            return True
        if asset_data.get('intune_device_id'):
            return True
        if asset_data.get('azure_ad_id'):
            return True
        dns_hostname = asset_data.get('dns_hostname', '')
        if dns_hostname and not dns_hostname.startswith('Device-') and dns_hostname not in ['', '_gateway']:
            return True
        name = (asset_data.get('name') or '').strip()
        if name and not name.lower().startswith('device-'):
            return True
        return bool(asset_data.get('asset_tag'))

    def _assign_model_manufacturer_category(self, payload: Dict, asset_data: Dict):
        """Determine and assign manufacturer, model, and category, creating them if necessary."""
        manufacturer_name, model_name = self._extract_mfr_and_model_names(asset_data)

        if self.debug:
            print(f"Processing model for asset '{asset_data.get('name', 'Unknown')}'. Manufacturer: '{manufacturer_name}', Model: '{model_name}'")
            if not manufacturer_name:
                print(f"WARNING: Missing manufacturer for asset: {asset_data.get('name', 'Unknown')}")
            if not model_name:
                print(f"WARNING: Missing model for asset: {asset_data.get('name', 'Unknown')}")

        is_generic_model_name = normalize_for_comparison(model_name) in [normalize_for_comparison(m['name']) for m in MODELS if 'Generic' in m['name']]

        if manufacturer_name and model_name and not is_generic_model_name:
            self._handle_specific_model(payload, asset_data, manufacturer_name, model_name)

        if 'model_id' not in payload:
            self._assign_generic_model(payload, asset_data)

    def _extract_mfr_and_model_names(self, asset_data: Dict) -> tuple[str, str]:
        """Extracts and cleans manufacturer and model names from asset data."""
        raw_mfr = asset_data.get('manufacturer')
        raw_model = asset_data.get('model')

        if isinstance(raw_mfr, dict):
            raw_mfr = raw_mfr.get('name') or ''
        if isinstance(raw_model, dict):
            raw_model = raw_model.get('name') or raw_model.get('model_number') or ''

        return str(raw_mfr or '').strip(), str(raw_model or '').strip()

    def _handle_specific_model(self, payload: Dict, asset_data: Dict, manufacturer_name: str, model_name: str):
        """Handles the logic for finding, creating, and assigning a specific model."""
        manufacturer = self.manufacturer_service.get_or_create({'name': manufacturer_name})
        if not manufacturer:
            return

        payload['manufacturer_id'] = manufacturer['id']
        category_obj = self._determine_category(asset_data)
        if not category_obj:
            return

        payload['category_id'] = category_obj['id']
        fieldset = self._determine_fieldset(category_obj, asset_data)

        full_model_name = self._build_full_model_name(manufacturer_name, model_name)

        model = self._get_or_create_model(full_model_name, manufacturer, category_obj, fieldset, model_name)

        if model:
            payload['model_id'] = model['id']
            self._update_model_if_needed(model, category_obj, fieldset)

    def _determine_fieldset(self, category_obj: Dict, asset_data: Dict) -> Optional[Dict]:
        """Determines the correct fieldset based on the asset's category."""
        category_name = category_obj.get('name') if isinstance(category_obj, dict) else str(category_obj)
        fieldset_map = {
            'Laptops': 'Managed and Discovered Assets', 'Desktops': 'Managed and Discovered Assets',
            'Mobile Phones': 'Managed and Discovered Assets', 'Tablets': 'Managed and Discovered Assets',
            'IoT Devices': 'Managed and Discovered Assets', 'Servers': 'Managed and Discovered Assets',
            'Virtual Machines (On-Premises)': 'Managed and Discovered Assets',
            'Cloud Resources': 'Cloud Resources (Azure)', 'Switches': 'Network Infrastructure',
            'Routers': 'Network Infrastructure', 'Firewalls': 'Network Infrastructure',
            'Access Points': 'Network Infrastructure', 'Network Devices': 'Network Infrastructure',
            'Printers': 'Discovered Assets (Nmap Only)',
        }
        fieldset_name = fieldset_map.get(category_name, 'Managed and Discovered Assets')
        fieldset = self.fieldset_service.get_by_name(fieldset_name)

        if not fieldset:
            print(f"[ERROR] Fieldset '{fieldset_name}' not found in Snipe-IT. Please ensure it exists.")
            print(f"  Asset '{asset_data.get('name', 'Unknown')}' may have issues with custom fields.")
        return fieldset

    def _build_full_model_name(self, manufacturer_name: str, model_name: str) -> str:
        """Constructs the full model name, avoiding manufacturer duplication."""
        norm_model = normalize_for_comparison(model_name)
        norm_mfr = normalize_for_comparison(manufacturer_name)
        if norm_model.startswith(norm_mfr) or norm_mfr.startswith(norm_model):
            return model_name
        return f"{manufacturer_name} {model_name}"

    def _get_or_create_model(self, full_model_name: str, manufacturer: Dict, category: Dict, fieldset: Optional[Dict], model_number: str) -> Optional[Dict]:
        """Finds an existing model by name or creates a new one."""
        model = self.model_service.get_by_name(full_model_name)
        if model:
            return model

        if self.debug:
            print(f"[_get_or_create_model] Model '{full_model_name}' not found. Attempting to create...")

        model_data = {
            'name': full_model_name,
            'manufacturer_id': manufacturer['id'],
            'category_id': category['id'],
            'model_number': model_number
        }
        if full_model_name == model_number:
            model_data.pop('model_number', None)
        if fieldset:
            model_data['fieldset_id'] = fieldset['id']

        try:
            new_model = self.model_service.create(model_data)
            if new_model:
                if self.debug:
                    print(f"[_get_or_create_model] Successfully created model: {full_model_name} (ID: {new_model.get('id')})")
                return new_model
            else:
                # Handle API error or race condition where another process created it
                error_response = getattr(self.model_service, 'last_error', "No specific error message.")
                print(f"[_get_or_create_model] ERROR: Model creation failed for '{full_model_name}'. API Error: {error_response}")
                print(f"[_get_or_create_model] WARNING: Retrying lookup for '{full_model_name}'...")
                self.model_service.get_all(refresh_cache=True)
                return self.model_service.get_by_name(full_model_name)
        except Exception as e:
            print(f"[_get_or_create_model] ERROR: Exception during model creation for '{full_model_name}': {str(e)}")
            return None

    def _update_model_if_needed(self, model: Dict, category: Dict, fieldset: Optional[Dict]):
        """Updates an existing model's category or fieldset if they are incorrect."""
        update_payload = {}
        if category and model.get('category', {}).get('id') != category['id']:
            update_payload['category_id'] = category['id']

        current_fieldset_id = (model.get('fieldset') or {}).get('id')
        target_fieldset_id = fieldset['id'] if fieldset else None

        if target_fieldset_id and current_fieldset_id != target_fieldset_id:
            update_payload['fieldset_id'] = target_fieldset_id

        if update_payload:
            if self.debug:
                old_category = (model.get('category') or {}).get('name')
                old_fieldset = (model.get('fieldset') or {}).get('name')
                new_fieldset_name = fieldset.get('name') if fieldset else 'None'
                print(f"[_update_model_if_needed] Updating model '{model.get('name')}'")
                print(f"  Category: '{old_category}' -> '{category['name']}'")
                print(f"  Fieldset: '{old_fieldset}' -> '{new_fieldset_name}'")
            self.model_service.update(model['id'], update_payload)

    def _assign_generic_model(self, payload: Dict, asset_data: Dict):
        """Assigns a generic model and ensures it has the correct fieldset."""
        if 'model_id' not in payload:
            device_type = str(asset_data.get('device_type') or '').lower()
            generic_model_name = self._determine_model_name(device_type)
            generic_model_obj = self.model_service.get_by_name(generic_model_name)
            
            if self.debug:
                print(f"No specific model assigned. Looking for generic: '{generic_model_name}'")

            if generic_model_obj:
                payload['model_id'] = generic_model_obj['id']
                # Set category from generic model if not already set
                if 'category_id' not in payload and generic_model_obj.get('category'):
                    payload['category_id'] = generic_model_obj.get('category', {}).get('id')
                    if self.debug:
                        print(f"Assigned generic model ID: {payload['model_id']}")

                # Ensure assets get the correct fieldset based on their source
                fieldset_service = self.fieldset_service
                source = asset_data.get('_source', 'nmap')
                
                if source == 'microsoft365':
                    target_fieldset_name = 'Managed and Discovered Assets'
                else: # Default for nmap or other simple discovery
                    target_fieldset_name = 'Discovered Assets (Nmap Only)'

                target_fieldset = fieldset_service.get_by_name(target_fieldset_name)
                
                current_fieldset_id = (generic_model_obj.get('fieldset') or {}).get('id')
                target_fieldset_id = target_fieldset.get('id') if target_fieldset else None

                if target_fieldset_id and current_fieldset_id != target_fieldset_id:
                    if self.debug:
                        print(f"[_assign_generic_model] Updating generic model '{generic_model_name}' to use fieldset '{target_fieldset_name}'.")
                    update_payload = {
                        'fieldset_id': target_fieldset_id,
                        'manufacturer_id': (generic_model_obj.get('manufacturer') or {}).get('id')
                    }
                    self.model_service.update(generic_model_obj['id'], update_payload)
                elif not target_fieldset:
                    print(f"[ERROR] Could not find the required fieldset '{target_fieldset_name}' in Snipe-IT.")

            else:
                raise ValueError(
                    f"FATAL: The required generic model '{generic_model_name}' was not found in Snipe-IT. "
                    f"Please ensure the initialization script has been run and the model exists."
                )
    
    def _populate_standard_fields(self, payload: Dict, asset_data: Dict, is_update: bool):
        """Populate standard, non-custom fields in the payload."""
        standard_fields = ['name', 'asset_tag', 'serial', 'notes']
        for field in standard_fields:
            if field in asset_data and asset_data[field]:
                payload[field] = asset_data[field]
        
        # MAC ADDRESS (built-in field)
        if 'mac_addresses' in asset_data and asset_data['mac_addresses']:
            macs = asset_data['mac_addresses']
            if isinstance(macs, str):
                # Take first MAC for built-in field
                first_mac = macs.split('\n')[0] if '\n' in macs else macs
                if first_mac:
                    payload['mac_address'] = normalize_mac(first_mac.strip())
        
        # AUTO-GENERATE ASSET TAG for new assets
        if not is_update and 'asset_tag' not in payload:
            payload['asset_tag'] = self._generate_asset_tag(asset_data)
       
        # LOCATION
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
        
        #  STATUS
        self._determine_status(payload, asset_data)
    
    def _hydrate_field_map(self):
        """
        Builds a map from our internal config key (e.g., 'last_seen_ip') to the
        server's actual database column name (e.g., '_snipeit_last_seen_ip_1').
        """
        if not AssetMatcher._hydrated:
            name_to_key_map = {normalize_for_comparison(value.get('name', '')): key
            for key, value in CUSTOM_FIELDS.items()}
            
            all_fields_from_server = self.field_service.get_all(refresh_cache=True) or []
            
            if all_fields_from_server and self.debug:
                print(f"[DEBUG] Sample field structure: {all_fields_from_server[0]}")
                print(f"[DEBUG] Available keys: {list(all_fields_from_server[0].keys())}")
                    
            for server_field in all_fields_from_server:
                field_name = normalize_for_comparison(server_field.get('name') or '')
                internal_key = name_to_key_map.get(field_name)
                if not internal_key:
                    continue

                db_column_str = server_field.get('db_column_name')
                if db_column_str:
                    AssetMatcher._custom_field_map[internal_key] = db_column_str
            
            if self.debug:
                print(f"[DEBUG] Hydrated {len(AssetMatcher._custom_field_map)} custom field mappings.")
                if len(AssetMatcher._custom_field_map) < len(CUSTOM_FIELDS):
                    missing = [k for k in CUSTOM_FIELDS if k not in AssetMatcher._custom_field_map]
                    print(f"[WARNING] Could not find server mapping for keys: {missing}")
            AssetMatcher._hydrated = True
        
    def _populate_custom_fields(self, payload: Dict, asset_data: Dict):
        """Populate custom fields into the main payload using their DB column names."""

        BOOLEAN_TEXT_FIELDS = {field_key for field_key, field_def in CUSTOM_FIELDS.items() if field_def['format'] == 'BOOLEAN'}
        
        if not AssetMatcher._hydrated:
            self._hydrate_field_map()
            
        for field_key, field_def in CUSTOM_FIELDS.items():
            if field_key in asset_data and asset_data[field_key] is not None:
                
                db_key = AssetMatcher._custom_field_map.get(field_key)
                if not db_key:
                    if self.debug:
                        print(f"[WARNING] No DB key for custom field '{field_def.get('name')}'. Skipping.")
                    continue

                value = asset_data[field_key]
                if isinstance(value, str) and value.strip() in ["", "Unknown"]:
                    continue

                if field_key in BOOLEAN_TEXT_FIELDS:
                    if isinstance(value, bool):
                        value = "1" if value else "0"
                    elif isinstance(value, int):
                        value = "1" if value == 1 else "0"
                    elif isinstance(value, str):
                        if value.lower() in ('true', '1', 'yes', 'on'):
                            value = "1"
                        elif value.lower() in ('false', '0', 'no', 'off'):
                            value = "0"
                
                    if self.debug:
                        print(f"[DEBUG] Boolean field '{field_key}' converted to: '{value}'")
                    
                elif field_def['element'] == 'textarea' and isinstance(value, (dict, list)):
                    value = json.dumps(value, indent=2)
                elif isinstance(value, dict):
                    value = value['name'] or json.dumps(value)
                elif isinstance(value, list):
                    value = ', '.join(map(str, value))
                
                payload[db_key] = value
                
                if self.debug:
                    print(f"[DEBUG] Setting custom field '{db_key}' = '{value}'")
                
    def _determine_status(self, payload: Dict, asset_data: Dict):
        """Determines and sets the status_id for the asset."""
        if 'status_id' in payload:
            return

        # Check if this is a low-information asset (IP only)
        is_ip_only_asset = (
            asset_data.get('last_seen_ip') and
            not asset_data.get('serial') and
            not asset_data.get('mac_addresses') and
            not asset_data.get('intune_device_id')
        )

        source_for_status = (asset_data.get('_source') or asset_data.get('last_update_source') or 'unknown')
        status_map = {
            'microsoft365': 'Managed - M365',
            'nmap': 'Discovered - Nmap',
            'snmp': 'On-Premise',
        }

        status_name = 'Discovered - Needs Review' if is_ip_only_asset and source_for_status == 'nmap' else status_map.get(source_for_status, 'Unknown')

        status = self.status_service.get_by_name(status_name)
        if status:
            payload['status_id'] = status['id']

    def _initialize_results(self) -> Dict:
        """Returns a clean dictionary for tracking sync results."""
        return {'created': 0, 'updated': 0, 'failed': 0, 'skipped_insufficient_data': 0, 'assets': []}

    def _determine_category(self, asset_data: Dict) -> str:
        """Determine asset category based on data by calling the AssetCategorizer."""
        classification = AssetCategorizer.categorize(asset_data)
        # Store device_type from categorization for later logic
        asset_data['device_type'] = classification.get('device_type')
        
        if self.debug:
            print(f"[_determine_category] Categorization for '{asset_data.get('name')}': {classification}")
        
        category_value = classification.get('category', 'Other Assets')
        if isinstance(category_value, dict):
            return category_value
    
        category_obj = self.category_service.get_by_name(category_value)
        if category_obj:
            return category_obj
        
        # Fallback to a default category if the determined one isn't found
        fallback_obj = self.category_service.get_by_name('Other Assets')
        return fallback_obj if fallback_obj else {'id': 18, 'name': 'Other Assets'}
        
    def _generate_asset_tag(self, asset_data: Dict) -> str:
        """Generate a unique asset tag."""
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