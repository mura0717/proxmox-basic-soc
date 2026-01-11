"""
Snipe-IT Payload Builder Module
"""

import json
import os
import hashlib
from typing import Dict, Any, Optional
from datetime import datetime

from proxmox_soc.builders.base_builder import BasePayloadBuilder, BuildResult
from proxmox_soc.states.base_state import StateResult
from proxmox_soc.snipe_it.snipe_api.services.categories import CategoryService
from proxmox_soc.snipe_it.snipe_api.services.manufacturers import ManufacturerService
from proxmox_soc.snipe_it.snipe_api.services.models import ModelService
from proxmox_soc.snipe_it.snipe_api.services.status_labels import StatusLabelService
from proxmox_soc.snipe_it.snipe_api.services.locations import LocationService
from proxmox_soc.snipe_it.snipe_api.services.fields import FieldService
from proxmox_soc.snipe_it.snipe_api.services.fieldsets import FieldsetService
from proxmox_soc.asset_engine.asset_categorizer import AssetCategorizer
from proxmox_soc.config.snipe_schema import CUSTOM_FIELDS, MODELS
from proxmox_soc.utils.mac_utils import normalize_mac
from proxmox_soc.utils.text_utils import normalize_for_comparison


class SnipePayloadBuilder(BasePayloadBuilder):
    """
    Handles all Snipe-IT specific payload formatting.
    """
    
    _custom_field_map: Dict[str, str] = {}
    _hydrated = False
    
    def __init__(self):
        self.status_service = StatusLabelService()
        self.category_service = CategoryService()
        self.manufacturer_service = ManufacturerService()
        self.model_service = ModelService()
        self.location_service = LocationService()
        self.field_service = FieldService()
        self.fieldset_service = FieldsetService()
        self.debug = os.getenv('SNIPE_BUILDER_DEBUG', '0') == '1'
        
        if not SnipePayloadBuilder._hydrated:
            self._hydrate_field_map()
    
    def build(self, asset_data: Dict, state_result: StateResult) -> BuildResult:
        """Build the final Snipe-IT JSON payload."""
        is_update = state_result.action == 'update'
        
        # Merge with existing data if updating
        if is_update and state_result.existing:
            working_data = self._merge_with_existing(
                state_result.existing, 
                asset_data, 
                asset_data.get('_source', 'unknown')
            )
        else:
            working_data = asset_data.copy()
        
        # Name Priority
        if working_data.get('host_name'):
            working_data['name'] = working_data['host_name']

        payload = {}
        self._assign_model_manufacturer_category(payload, working_data)
        self._populate_standard_fields(payload, working_data, is_update)
        self._populate_custom_fields(payload, working_data)
        
        return BuildResult(
            payload=payload,
            asset_id=state_result.asset_id,
            action=state_result.action,
            snipe_id=int(state_result.asset_id) if state_result.action == 'update' and state_result.asset_id.isdigit() else None,
            metadata={
                'source': asset_data.get('_source'),
                'name': payload.get('name'),
            }
        )

    # --- 1. MODEL / MANUFACTURER / CATEGORY LOGIC ---

    def _assign_model_manufacturer_category(self, payload: Dict, asset_data: Dict):
        category_obj = self._determine_category(asset_data)
        mfr_name, model_name = self._extract_mfr_and_model_names(asset_data)

        if self.debug:
            print(f"Processing model for asset '{asset_data.get('name', 'Unknown')}'. Manufacturer: '{mfr_name}', Model: '{model_name}'")

        is_generic = normalize_for_comparison(model_name) in [
            normalize_for_comparison(m['name']) for m in MODELS if 'Generic' in m['name']
        ]

        if mfr_name and model_name and not is_generic:
            self._handle_specific_model(payload, asset_data, mfr_name, model_name, category_obj)
        else:
            self._assign_generic_model(payload, asset_data, category_obj)

        if category_obj and 'category_id' not in payload:
            payload['category_id'] = category_obj['id']

    def _handle_specific_model(self, payload: Dict, asset_data: Dict, mfr_name: str, model_name: str, category_obj: Dict):
        manufacturer = self.manufacturer_service.get_or_create({'name': mfr_name})
        if not manufacturer or not category_obj: return
        
        payload['manufacturer_id'] = manufacturer['id']
        payload['category_id'] = category_obj['id']
        fieldset = self._determine_fieldset(category_obj, asset_data)

        full_model_name = self._build_full_model_name(mfr_name, model_name)
        model = self._get_or_create_model(full_model_name, manufacturer, category_obj, fieldset)

        if model:
            payload['model_id'] = model['id']

    def _assign_generic_model(self, payload: Dict, asset_data: Dict, category_obj: Optional[Dict] = None):
        if 'model_id' in payload: return
        
        device_type = str(asset_data.get('device_type') or '').lower()
        generic_name = self._determine_model_name(device_type)
        generic_model = self.model_service.get_by_name(generic_name)
        
        if generic_model:
            payload['model_id'] = generic_model['id']
            if category_obj:
                payload['category_id'] = category_obj['id']
            elif 'category_id' not in payload and generic_model.get('category'):
                payload['category_id'] = generic_model.get('category', {}).get('id')

    def _determine_category(self, asset_data: Dict) -> Dict:
        classification = AssetCategorizer.categorize(asset_data)
        asset_data['device_type'] = classification.get('device_type')
        
        if self.debug:
            print(f"[_determine_category] Categorization for '{asset_data.get('name')}': {classification}")
        
        cat_name = classification.get('category', 'Other Assets')
        if isinstance(cat_name, dict): cat_name = cat_name.get('name')
        
        return self.category_service.get_or_create({'name': cat_name, 'category_type': 'asset'})

    def _determine_model_name(self, device_type: str) -> str:
        device_type = device_type.lower()
        model_map = {
            'server': 'Generic Server', 'camera': 'Generic Camera', 'desktop': 'Generic Desktop',
            'laptop': 'Generic Laptop', 'switch': 'Generic Switch', 'router': 'Generic Router',
            'firewall': 'Generic Firewall', 'access point': 'Generic Access Point', 'printer': 'Generic Printer'
        }
        for key, name in model_map.items():
            if key in device_type: return name
        return 'Generic Unknown Device'

    def _determine_fieldset(self, category_obj: Dict, asset_data: Dict) -> Optional[Dict]:
        cat_name = category_obj.get('name') if isinstance(category_obj, dict) else str(category_obj)
        fieldset_name = 'Managed and Discovered Assets'
        
        if cat_name in ['Switches', 'Routers', 'Firewalls', 'Access Points', 'Cameras']:
            fieldset_name = 'Network Infrastructure'
        elif cat_name == 'Printers':
            fieldset_name = 'Discovered Assets (Nmap Only)'
            
        return self.fieldset_service.get_by_name(fieldset_name)

    def _build_full_model_name(self, mfr: str, model: str) -> str:
        if normalize_for_comparison(model).startswith(normalize_for_comparison(mfr)):
            return model
        return f"{mfr} {model}"

    def _get_or_create_model(self, name: str, mfr: Dict, cat: Dict, fieldset: Optional[Dict]) -> Optional[Dict]:
        model = self.model_service.get_by_name(name)
        if model: return model
        
        if self.debug:
            print(f"[_get_or_create_model] Model '{name}' not found. Attempting to create...")
        
        data = {'name': name, 'manufacturer_id': mfr['id'], 'category_id': cat['id'], 'model_number': name}
        if fieldset: data['fieldset_id'] = fieldset['id']
        
        if self.debug:
            print(f"[_get_or_create_model] Successfully created model: {data['name']} under manufacturer '{mfr['name']}' and category '{cat['name']}'")
        
        return self.model_service.create(data)    
    
    def _merge_with_existing(self, existing: Dict, new_data: Dict, scan_type: str) -> Dict:
        """Merge new scan data with existing asset data."""
        merged = self._flatten_existing_asset(existing)
        
        priority_fields = {
            'nmap': ['last_seen_ip', 'nmap_last_scan', 'nmap_open_ports', 
                     'nmap_services', 'nmap_os_guess', 'open_ports_hash'],
            'microsoft365': ['intune_last_sync', 'intune_compliance', 
                            'primary_user_upn', 'primary_user_email'],
        }.get(scan_type, [])
        
        for key, value in new_data.items():
            if value in (None, '', []):
                continue
            if key in priority_fields or not merged.get(key):
                merged[key] = value
        
        merged['_source'] = scan_type
        return merged

    def _flatten_existing_asset(self, existing: Dict) -> Dict:
        """Flatten Snipe-IT API response to simple key-value pairs."""
        flattened = {}
        
        for key, value in existing.items():
            if key == 'custom_fields':
                continue
            elif isinstance(value, dict):
                flattened[key] = value.get('name') or value.get('id')
            else:
                flattened[key] = value
        
        for label, field_data in existing.get('custom_fields', {}).items():
            value = field_data.get('value') if isinstance(field_data, dict) else field_data
            for key, field_def in CUSTOM_FIELDS.items():
                if field_def.get('name') == label:
                    flattened[key] = value
                    break
        
        return flattened
    
    def _extract_mfr_and_model_names(self, asset_data: Dict) -> tuple:
        mfr = asset_data.get('manufacturer')
        model = asset_data.get('model')
        mfr_str = mfr.get('name') if isinstance(mfr, dict) else mfr
        model_str = model.get('name') if isinstance(model, dict) else model
        return str(mfr_str or '').strip(), str(model_str or '').strip()

    # --- 2. STANDARD FIELDS ---

    def _populate_standard_fields(self, payload: Dict, asset_data: Dict, is_update: bool):
        for field in ['name', 'asset_tag', 'serial', 'notes']:
            if asset_data.get(field): payload[field] = asset_data[field]
            
        if asset_data.get('mac_addresses'):
            macs = asset_data['mac_addresses']
            first_mac = macs.split('\n')[0] if isinstance(macs, str) else macs
            if first_mac: payload['mac_address'] = normalize_mac(first_mac.strip())
            
        if not is_update and 'asset_tag' not in payload:
            payload['asset_tag'] = self._generate_asset_tag(asset_data)
            
        self._assign_location(payload, asset_data)
        self._determine_status(payload, asset_data)

    def _determine_status(self, payload: Dict, asset_data: Dict):
        if 'status_id' in payload: return
        source = asset_data.get('_source', 'unknown')
        status_name = 'Discovered - Nmap' if source == 'nmap' else 'Unknown'
        if source in ['microsoft365', 'intune']: status_name = 'Managed - M365'
        
        status = self.status_service.get_by_name(status_name)
        if status: payload['status_id'] = status['id']

    def _assign_location(self, payload: Dict, asset_data: Dict):
        loc_name = asset_data.get('location')
        if not loc_name: return
        if isinstance(loc_name, dict): loc_name = loc_name.get('name')
        
        location = self.location_service.get_by_name(loc_name)
        if not location: location = self.location_service.create({'name': loc_name})
        if location: payload['location_id'] = location['id']

    def _generate_asset_tag(self, asset_data: Dict) -> str:
        ts = datetime.now().strftime('%Y%m%d%H%M%S')
        hash_input = json.dumps(asset_data, sort_keys=True, default=str)
        hash_part = hashlib.md5(hash_input.encode()).hexdigest()[:6].upper()
        return f"AUTO-{ts}-{hash_part}"

    # --- 3. CUSTOM FIELDS ---

    def _populate_custom_fields(self, payload: Dict, asset_data: Dict):
        if not SnipePayloadBuilder._hydrated: self._hydrate_field_map()
        
        for field_key, field_def in CUSTOM_FIELDS.items():
            val = asset_data.get(field_key)
            db_key = SnipePayloadBuilder._custom_field_map.get(field_key)
            
            if val is not None and db_key:
                if isinstance(val, str) and not val.strip(): continue
                formatted = self._format_custom_value(field_key, val, field_def)
                if formatted is not None: payload[db_key] = formatted

    def _hydrate_field_map(self):
        if SnipePayloadBuilder._hydrated: return
        config_map = {normalize_for_comparison(v['name']): k for k, v in CUSTOM_FIELDS.items()}
        server_fields = self.field_service.get_all(refresh_cache=True) or []
        for field in server_fields:
            name = normalize_for_comparison(field.get('name', ''))
            key = config_map.get(name)
            if key and field.get('db_column_name'):
                SnipePayloadBuilder._custom_field_map[key] = field['db_column_name']
        if self.debug:
                print(f"[DEBUG] Hydrated {len(SnipePayloadBuilder._custom_field_map)} custom field mappings.")
                if len(SnipePayloadBuilder._custom_field_map) < len(CUSTOM_FIELDS):
                    missing = [k for k in CUSTOM_FIELDS if k not in SnipePayloadBuilder._custom_field_map]
                    print(f"[WARNING] Could not find server mapping for keys: {missing}")
        SnipePayloadBuilder._hydrated = True

    def _format_custom_value(self, key: str, val: Any, field_def: Dict) -> Optional[str]:
        if field_def.get('format') == 'BOOLEAN':
            return "1" if str(val).lower() in ('true', '1', 'yes', 'on') else "0"
        if isinstance(val, (dict, list)):
            return json.dumps(val, indent=2) if field_def.get('element') == 'textarea' else str(val)
        return str(val)