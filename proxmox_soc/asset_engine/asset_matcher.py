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

from snipe_api.services.status_labels import StatusLabelService
from snipe_api.services.categories import CategoryService
from snipe_api.services.manufacturers import ManufacturerService
from snipe_api.services.models import ModelService
from snipe_api.services.assets import AssetService
from snipe_api.services.locations import LocationService
from snipe_api.services.fields import FieldService
from snipe_api.services.fieldsets import FieldsetService
from asset_engine.asset_categorizer import AssetCategorizer
from asset_engine.asset_finder import AssetFinder
from config.snipe_schema import CUSTOM_FIELDS, MODELS
from config.network_config import STATIC_IP_MAP
from debug.tools.asset_debug_logger import debug_logger
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
    
    def process_scan_data(self, scan_type: str, scan_data: List[Dict]) -> Dict:
        """Process scan data from various sources (main entry point).
        Args:
            scan_type: Type of scan (nmap, snmp, intune, etc.)
            scan_data: List of discovered assets
        Returns:
            Dictionary with processing results
        """
        results = self._initialize_results()
        return self._process_assets(scan_type, scan_data, results)

    def clear_all_caches(self):
        """Clears the internal caches of all services to ensure fresh data."""
        print("Clearing all local service caches...")
        self.asset_service._cache.clear()
        self.status_service._cache.clear()
        self.category_service._cache.clear()
        self.manufacturer_service._cache.clear()
        self.model_service._cache.clear()
        self.finder._all_assets_cache = None
    
    def find_existing_asset(self, asset_data: Dict) -> Optional[Dict]:
        """Find an existing asset using a prioritized chain of matching strategies."""
        if self.debug:
            print(f"[SEARCHING EXISTING ASSET]: {asset_data.get('name', 'Unknown')}")

        # The order of these calls defines the matching priority.
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
        """Merge data from multiple sources with priority handling."""
        source_priority = {
            'intune': 1,      # Highest priority
            'teams': 2,       #
            'nmap': 3,        #
            'snmp': 4,        #
            'existing': 99    # Lowest priority
        }

        # Sort sources from lowest to highest priority, so higher priority data overwrites lower.
        sorted_sources = sorted(data_sources, key=lambda d: source_priority.get(d.get('_source', 'existing'), 99), reverse=True)

        merged = {}
        for source_data in sorted_sources:
            for key, value in source_data.items():
                if key.startswith('_') and key != '_source':
                    continue
                # Add the value if key doesn't exist, OR if new value is truthy.
                # We also allow overwriting with 0 or False (but not None/Empty string).
                if key not in merged or (value is not None and value != ''):
                    merged[key] = value
        return merged

    # --- Core Orchestration (Private) ---

    def _process_assets(self, scan_type: str, scan_data: List[Dict], results: Dict) -> Dict:
        """Iterate through scan data and process each asset."""
        for asset_data in scan_data:
            asset_data['_source'] = scan_type

            self._enrich_with_static_map(asset_data) # Enrich with static IP mapping data first.

            existing = self.find_existing_asset(asset_data)
            
            if existing:
                
                flattened_existing = {**existing} # Create a copy
                if isinstance(flattened_existing.get('model'), dict):
                    flattened_existing['model'] = flattened_existing['model'].get('name')
                if isinstance(flattened_existing.get('manufacturer'), dict):
                    flattened_existing['manufacturer'] = flattened_existing['manufacturer'].get('name')
                    
                merged_data = self.merge_asset_data({'_source': 'existing', **flattened_existing}, asset_data)
                # Ensure the new scan's source is preserved for categorization.
                merged_data['_source'] = scan_type

                if self._update_asset(existing['id'], merged_data, scan_type):
                    results['updated'] += 1
                    results['assets'].append({'id': existing['id'], 'action': 'updated', 'name': merged_data.get('name', 'Unknown')})
                else:
                    results['failed'] += 1
            else:
                # Create a new asset if it has sufficient data.
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

    # --- Payload Preparation (Private) ---
    
    def _prepare_asset_payload(self, asset_data: Dict, is_update: bool = False) -> Dict:
        """Orchestrate the preparation of the asset data payload for the Snipe-IT API."""
        payload = {}
        
        # Use trusted hostname from static map as the definitive asset name.
        if asset_data.get('host_name'):
            asset_data['name'] = asset_data['host_name']

        self._assign_model_manufacturer_category(payload, asset_data)
        self._populate_standard_fields(payload, asset_data, is_update)
        self._populate_custom_fields(payload, asset_data)
        
        return payload

    def _assign_model_manufacturer_category(self, payload: Dict, asset_data: Dict):
        """Determine and assign manufacturer, model, and category."""
        
        # 1. Always run categorization first to get the device_type and target category.
        category_obj = self._determine_category(asset_data)
        
        manufacturer_name, model_name = self._extract_mfr_and_model_names(asset_data)
        if debug_logger.is_enabled:        
            print(f"Processing model for asset '{asset_data.get('name', 'Unknown')}'. Manufacturer: '{manufacturer_name}', Model: '{model_name}'")

        is_generic_model_name = normalize_for_comparison(model_name) in [normalize_for_comparison(m['name']) for m in MODELS if 'Generic' in m['name']]

        # 3. If we have specific hardware data, handle the specific model. Otherwise, assign a generic one.
        if manufacturer_name and model_name and not is_generic_model_name:
            self._handle_specific_model(payload, asset_data, manufacturer_name, model_name, category_obj)
        else:
            self._assign_generic_model(payload, asset_data, category_obj)

        # 4. Final fallback to ensure category is set if model logic somehow failed to set it.
        if category_obj and 'category_id' not in payload: # Failsafe
            payload['category_id'] = category_obj['id']

    def _handle_specific_model(self, payload: Dict, asset_data: Dict, manufacturer_name: str, model_name: str, category_obj: Dict):
        """Handles the logic for finding, creating, and assigning a specific model."""
        manufacturer = self.manufacturer_service.get_or_create({'name': manufacturer_name})
        if not manufacturer:
            return
        
        if not category_obj:
            return
        
        payload['manufacturer_id'] = manufacturer['id']
        payload['category_id'] = category_obj['id']
        fieldset = self._determine_fieldset(category_obj, asset_data)

        full_model_name = self._build_full_model_name(manufacturer_name, model_name)
        model = self._get_or_create_model(full_model_name, manufacturer, category_obj, fieldset, model_name)

        if model:
            payload['model_id'] = model['id']
            
            # Model Repair Logic: Corrects mismatches on existing models.
            updates_needed = {}
            
            existing_mfr_id = (model.get('manufacturer') or {}).get('id')
            if existing_mfr_id != manufacturer.get('id'):
                updates_needed['manufacturer_id'] = manufacturer['id']

            existing_cat_id = (model.get('category') or {}).get('id')
            if existing_cat_id != category_obj.get('id'):
                updates_needed['category_id'] = category_obj['id']

            target_fieldset_id = fieldset['id'] if fieldset else None
            existing_fieldset_id = (model.get('fieldset') or {}).get('id')
            if target_fieldset_id and existing_fieldset_id != target_fieldset_id:
                 updates_needed['fieldset_id'] = target_fieldset_id

            if updates_needed:
                print(f"   [REPAIR] Correcting metadata for model '{full_model_name}' (ID: {model['id']})")
                self.model_service.update(model['id'], updates_needed)

    def _assign_generic_model(self, payload: Dict, asset_data: Dict, category_obj: Optional[Dict] = None):
        """Assigns a generic model based on the pre-calculated device type."""
        if 'model_id' in payload: return

        device_type = str(asset_data.get('device_type') or '').lower()
        generic_model_name = self._determine_model_name(device_type)
        generic_model_obj = self.model_service.get_by_name(generic_model_name)
        
        if not generic_model_obj:
            print(f"[FATAL] Generic model '{generic_model_name}' not found.")
            return

        payload['model_id'] = generic_model_obj['id']
        updates_needed = {}

        # Enforce Category on the Generic Model.
        if category_obj:
            payload['category_id'] = category_obj['id']
            if (generic_model_obj.get('category') or {}).get('id') != category_obj['id']:
                updates_needed['category_id'] = category_obj['id']
        elif 'category_id' not in payload and generic_model_obj.get('category'):
             payload['category_id'] = generic_model_obj.get('category', {}).get('id')

        # Enforce Fieldset on the Generic Model.
        source = asset_data.get('_source', 'nmap')
        target_fieldset_name = 'Managed and Discovered Assets' if source == 'microsoft365' else 'Discovered Assets (Nmap Only)'
        target_fieldset = self.fieldset_service.get_by_name(target_fieldset_name)
        
        current_fieldset_id = (generic_model_obj.get('fieldset') or {}).get('id')
        target_fieldset_id = target_fieldset.get('id') if target_fieldset else None

        if target_fieldset_id and current_fieldset_id != target_fieldset_id:
            updates_needed['fieldset_id'] = target_fieldset_id

        if updates_needed:
            print(f"   [REPAIR] Correcting metadata for generic model '{generic_model_name}'")
            self.model_service.update(generic_model_obj['id'], updates_needed)
    
    def _populate_standard_fields(self, payload: Dict, asset_data: Dict, is_update: bool):
        """Populate standard, non-custom fields in the payload."""
        standard_fields = ['name', 'asset_tag', 'serial', 'notes']
        for field in standard_fields:
            if field in asset_data and asset_data[field]:
                payload[field] = asset_data[field]
        
        # Use the first MAC for the built-in 'mac_address' field.
        if 'mac_addresses' in asset_data and asset_data['mac_addresses']:
            macs = asset_data['mac_addresses']
            if isinstance(macs, str):
                first_mac = macs.split('\n')[0] if '\n' in macs else macs
                if first_mac:
                    payload['mac_address'] = normalize_mac(first_mac.strip())
        
        # Auto-generate an asset tag for new assets if one isn't provided.
        if not is_update and 'asset_tag' not in payload:
            payload['asset_tag'] = self._generate_asset_tag(asset_data)
       
        self._assign_location(payload, asset_data)
        self._determine_status(payload, asset_data)

    def _determine_fieldset(self, category_obj: Dict, asset_data: Dict) -> Optional[Dict]:
        """Determines the correct fieldset based on the asset's category name."""
        category_name = category_obj.get('name') if isinstance(category_obj, dict) else str(category_obj)
        fieldset_map = {
            'Laptops': 'Managed and Discovered Assets', 'Desktops': 'Managed and Discovered Assets',
            'Mobile Phones': 'Managed and Discovered Assets', 'Tablets': 'Managed and Discovered Assets',
            'IoT Devices': 'Managed and Discovered Assets', 'Servers': 'Managed and Discovered Assets',
            'Virtual Machines': 'Managed and Discovered Assets',
            'Cameras': 'Network Infrastructure',
            'Cloud Resources': 'Cloud Resources (Azure)', 'Switches': 'Network Infrastructure',
            'Routers': 'Network Infrastructure', 'Firewalls': 'Network Infrastructure',
            'Access Points': 'Network Infrastructure', 'Network Devices': 'Network Infrastructure',
            'Printers': 'Discovered Assets (Nmap Only)',
        }
        fieldset_name = fieldset_map.get(category_name, 'Managed and Discovered Assets')
        fieldset = self.fieldset_service.get_by_name(fieldset_name)

        if not fieldset:
            print(f"[ERROR] Fieldset '{fieldset_name}' not found. Asset '{asset_data.get('name', 'Unknown')}' may have issues with custom fields.")
        return fieldset
    
    def _populate_custom_fields(self, payload: Dict, asset_data: Dict):
        """Populate custom fields into the main payload using their DB column names."""

        if not AssetMatcher._hydrated:
            self._hydrate_field_map()
            
        for field_key, field_def in CUSTOM_FIELDS.items():
            if field_key in asset_data and asset_data[field_key] is not None:
                
                db_key = AssetMatcher._custom_field_map.get(field_key)
                if not db_key: continue

                value = asset_data[field_key]
                if isinstance(value, str) and not value.strip():
                    continue
                
                formatted_value = self._format_custom_field_value(field_key, value, field_def)
                if formatted_value is not None:
                    payload[db_key] = formatted_value

    # --- Data Lookup & Matching (Private) ---

    def _hydrate_field_map(self):
        """Map internal config keys to Snipe-IT's database column names for custom fields."""
        if not AssetMatcher._hydrated:
            name_to_key_map = {normalize_for_comparison(value.get('name', '')): key
            for key, value in CUSTOM_FIELDS.items()}
            
            all_fields_from_server = self.field_service.get_all(refresh_cache=True) or []
            
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
            'model_number': full_model_name  # To ensure uniqueness
        }
        if fieldset:
            model_data['fieldset_id'] = fieldset['id']

        try:
            new_model = self.model_service.create(model_data)
            if new_model:
                if self.debug:
                    print(f"[_get_or_create_model] Successfully created model: {full_model_name} (ID: {new_model.get('id')})")
                return new_model
            else:
                # Another process might have created it. Retry the lookup.
                print(f"[_get_or_create_model] WARNING: Retrying lookup for '{full_model_name}'...")
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

    def _determine_status(self, payload: Dict, asset_data: Dict):
        """Determines and sets the status_id for the asset."""
        if 'status_id' in payload:
            return

        # Check if this is a low-information asset (IP only).
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

    def _determine_category(self, asset_data: Dict) -> str:
        """Determine asset category based on data by calling the AssetCategorizer."""
        classification = AssetCategorizer.categorize(asset_data) # type: ignore
        # Store device_type back into asset_data for use in generic model assignment.
        asset_data['device_type'] = classification.get('device_type')
        
        if self.debug:
            print(f"[_determine_category] Categorization for '{asset_data.get('name')}': {classification}")
        
        category_name = classification.get('category', 'Other Assets')
        if isinstance(category_name, dict): # type: ignore
            category_name = category_name.get('name', 'Other Assets')

        category_obj = self.category_service.get_or_create({
            'name': category_name,
            'category_type': 'asset' # Default to 'asset' type on creation
        })

        if category_obj:
            return category_obj
        
    def _determine_model_name(self, device_type: str) -> str:
        """Determine model name based on device type"""
        device_type = device_type.lower()
        
        model_map = {
            'server': 'Generic Server',
            'camera': 'Generic Camera',
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

    def _assign_location(self, payload: Dict, asset_data: Dict):
        """Finds or creates a location and assigns its ID to the payload."""
        location_name = asset_data.get('location')
        if not location_name:
            return

        location_name_str = location_name.get('name') if isinstance(location_name, dict) else location_name
        location = self.location_service.get_by_name(location_name_str)
        if not location:
            print(f"  -> Location '{location_name}' not found. Creating it now...")
            location = self.location_service.create({'name': location_name})

        if location and location.get('id'):
            payload['location_id'] = location['id']
        else:
            print(f"  [ERROR] Failed to find or create location '{location_name}'. Asset will have no location.")

    # --- Utility Helpers (Private) ---

    def _initialize_results(self) -> Dict:
        """Returns a clean dictionary for tracking sync results."""
        return {'created': 0, 'updated': 0, 'failed': 0, 'skipped_insufficient_data': 0, 'assets': []}

    def _has_sufficient_data(self, asset_data: Dict) -> bool:
        """Determine if we have enough data to create a new asset."""
        # An IP-only asset will be created but flagged for review, so it's "sufficient".
        if asset_data.get('last_seen_ip') and not (asset_data.get('serial') or asset_data.get('mac_addresses') or asset_data.get('intune_device_id')):
            return True
        if asset_data.get('last_seen_ip') in STATIC_IP_MAP:
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

    def _enrich_with_static_map(self, asset_data: Dict):
        """If the asset's IP is in the static map, enrich the asset data with it."""
        ip_address = asset_data.get('last_seen_ip')
        if ip_address and ip_address in STATIC_IP_MAP:
            asset_data.update(STATIC_IP_MAP[ip_address])

    def _extract_mfr_and_model_names(self, asset_data: Dict) -> tuple[str, str]:
        """Extracts and cleans manufacturer and model names from asset data."""
        raw_mfr = asset_data.get('manufacturer')
        raw_model = asset_data.get('model')

        if isinstance(raw_mfr, dict):
            raw_mfr = raw_mfr.get('name') or ''
        if isinstance(raw_model, dict):
            raw_model = raw_model.get('name') or raw_model.get('model_number') or ''

        return str(raw_mfr or '').strip(), str(raw_model or '').strip()

    def _generate_asset_tag(self, asset_data: Dict) -> str:
        """Generate a unique asset tag."""
        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        hash_part = self.generate_asset_hash(asset_data)[:6].upper()
        return f"AUTO-{timestamp}-{hash_part}"

    def generate_asset_hash(self, identifiers: Dict) -> str:
        """Generate unique hash for asset identification"""
        hash_string = json.dumps(identifiers, sort_keys=True)
        return hashlib.md5(hash_string.encode()).hexdigest()

    def _format_custom_field_value(self, field_key: str, value: Any, field_def: Dict) -> Optional[str]:
        """Formats a value for a custom field based on its type."""
        BOOLEAN_TEXT_FIELDS = {k for k, v in CUSTOM_FIELDS.items() if v['format'] == 'BOOLEAN'}

        if field_key in BOOLEAN_TEXT_FIELDS:
            if isinstance(value, bool): return "1" if value else "0"
            if isinstance(value, int): return "1" if value == 1 else "0"
            if isinstance(value, str):
                if value.lower() in ('true', '1', 'yes', 'on'): return "1"
                if value.lower() in ('false', '0', 'no', 'off'): return "0"
        elif field_def['element'] == 'textarea' and isinstance(value, (dict, list)):
            return json.dumps(value, indent=2)
        elif isinstance(value, dict):
            return value.get('name') or json.dumps(value)
        return ', '.join(map(str, value)) if isinstance(value, list) else str(value)