#!/usr/bin/env python3
"""
Snipe-IT Setup Script
Initializes Snipe-IT with custom fields, fieldsets, status labels, categories, and locations
"""

import argparse
import time

from proxmox_soc.snipe_it.snipe_api.services.fields import FieldService
from proxmox_soc.snipe_it.snipe_api.services.fieldsets import FieldsetService
from proxmox_soc.snipe_it.snipe_api.services.manufacturers import ManufacturerService
from proxmox_soc.snipe_it.snipe_api.services.models import ModelService
from proxmox_soc.snipe_it.snipe_api.services.status_labels import StatusLabelService
from proxmox_soc.snipe_it.snipe_api.services.categories import CategoryService
from proxmox_soc.snipe_it.snipe_api.services.locations import LocationService
from proxmox_soc.snipe_it.snipe_api.services.crudbase import CrudBaseService
from proxmox_soc.config.snipe_schema import CUSTOM_FIELDS, CUSTOM_FIELDSETS, STATUS_LABELS, CATEGORIES, MANUFACTURERS, MODELS, LOCATIONS

class SnipeITSetup:
    """Main setup class for Snipe-IT configuration"""
    
    def __init__(self):
        self.field_service = FieldService()
        self.fieldset_service = FieldsetService()
        self.status_service = StatusLabelService()
        self.category_service = CategoryService()
        self.model_service = ModelService()
        self.manufacture_service = ManufacturerService()
        self.location_service = LocationService()
    
    def setup_all(self):
        """Run complete setup"""
        print("=" * 60)
        print("Starting Snipe-IT Setup")
        print("=" * 60)
        
        self.setup_status_labels()
        self.setup_categories()
        self.setup_locations()
        self.setup_manufacturers()
        self.setup_models()
        self.setup_fields()
        self.setup_fieldsets()
        self.associate_fields_to_fieldsets()
        
        print("\n" + "=" * 60)
        print("Setup Complete!")
        print("=" * 60)
    
    def setup_status_labels(self):
        """Create all status labels"""
        print("\n--- Setting up Status Labels ---")
        created, skipped = 0, 0
        
        for label_name, config in STATUS_LABELS.items():
            payload = {
                "name": label_name,
                "color": config.get("color", "#FFFFFF"),
                "type": config.get("type", "deployable"),
                "show_in_nav": config.get("show_in_nav", False),
                "default_label": config.get("default_label", False)
            }
            result = self.status_service.create_if_not_exists(payload)
            if result:
                created += 1
            else:
                skipped += 1
        
        print(f"✓ Status Labels: {created} created, {skipped} already existed")
    
    def setup_categories(self):
        """Create all categories"""
        print("\n--- Setting up Categories ---")
        created, skipped = 0, 0
        
        for category_name, config in CATEGORIES.items():
            payload = {
                "name": category_name,
                "category_type": config.get("category_type", "asset"),
                "use_default_eula": config.get("use_default_eula", False),
                "require_acceptance": config.get("require_acceptance", False),
                "checkin_email": config.get("checkin_email", False)
            }
            result = self.category_service.create_if_not_exists(payload)
            if result:
                created += 1
            else:
                skipped += 1
        
        print(f"✓ Categories: {created} created, {skipped} already existed")
    
    def setup_locations(self):
        """Create all locations"""
        print("\n--- Setting up Locations ---")
        created, skipped = 0, 0
        
        for location_name in LOCATIONS:
            result = self.location_service.create_if_not_exists({"name": location_name})
            if result:
                created += 1
            else:
                skipped += 1
        
        print(f"✓ Locations: {created} created, {skipped} already existed")
    
    def setup_manufacturers(self):
        """Create all common manufacturers"""
        print("\n--- Setting up Manufacturers ---")
        created, skipped = 0, 0
        for manufacturer_data in MANUFACTURERS:
            result = self.manufacture_service.create_if_not_exists({"name": manufacturer_data['name']})
            if result:
                created += 1
            else:
                skipped += 1
                
        print(f"✓ Manufacturers: {created} created, {skipped} already existed")
        
    def setup_models(self):
        """Create default model if not exists"""
        print("\n--- Setting up Default Model ---")
        created, skipped = 0, 0
        
        for model_data in MODELS:
            mfr = self.manufacture_service.get_by_name(model_data['manufacturer'])
            cat = self.category_service.get_by_name(model_data['category'])
            
            if mfr and cat:
                payload = {
                    "name": model_data['name'],
                    "manufacturer_id": mfr['id'],
                    "category_id": cat['id'],
                    "model_number": model_data.get('model_number', ''),
                }
                result = self.model_service.create_if_not_exists(payload)
                if result:
                    created += 1
                else:
                    skipped += 1
            else:
                if not mfr:
                    print(f"  ✗ Manufacturer '{model_data['manufacturer']}' not found for model '{model_data['name']}'. Skipping.")
                if not cat:
                    print(f"  ✗ Category '{model_data['category']}' not found for model '{model_data['name']}'. Skipping.")
                
        print(f"✓ Models: {created} created, {skipped} already existed")
    
    def setup_fields(self):
        """Create all custom fields"""
        print("\n--- Setting up Custom Fields ---")
        created, skipped = 0, 0
        
        for field_key, field_data in CUSTOM_FIELDS.items():
            result = self.field_service.create_if_not_exists(field_data)
            if result:
                created += 1
            else:
                skipped += 1
        
        print(f"✓ Fields: {created} created, {skipped} already existed")
    
    def setup_fieldsets(self):
        """Create all fieldsets"""
        print("\n--- Setting up Fieldsets ---")
        created, skipped = 0, 0
        
        for fieldset_name in CUSTOM_FIELDSETS.keys():
            result = self.fieldset_service.create_if_not_exists({"name": fieldset_name})
            if result:
                created += 1
            else:
                skipped += 1
        
        print(f"✓ Fieldsets: {created} created, {skipped} already existed")
    
    def associate_fields_to_fieldsets(self):
        """Associate fields with their fieldsets"""
        print("\n--- Associating Fields with Fieldsets ---")
        total_associations = 0
        
        for fieldset_name, field_keys in CUSTOM_FIELDSETS.items():
            associations = self.fieldset_service.setup_fieldset_associations(
                fieldset_name, field_keys, CUSTOM_FIELDS
            )
            total_associations += associations
            print(f"  ✓ {fieldset_name}: {associations} fields associated")
        
        print(f"✓ Total associations created: {total_associations}")
    
    
    def cleanup_all(self):
        """Remove all custom configuration"""
        print("=" * 60)
        print("Starting Cleanup")
        print("=" * 60)
        
        # Delete in an order that respects dependencies.
        # Note: Assets should be deleted before this script is run.
        self.cleanup_models()
        self.cleanup_fieldsets()
        self.cleanup_fields()
        self.cleanup_manufacturers()
        self.cleanup_locations()
        self.cleanup_categories()
        self.cleanup_status_labels()
        
        print("\n" + "=" * 60)
        print("Cleanup Complete!")
        print("=" * 60)
    
    def cleanup_fields(self):
        """Delete all custom fields"""
        print("\n--- Cleaning up Custom Fields ---")
        deleted = 0
        for field in self.field_service.get_all(limit=1000, refresh_cache=True):
            if self.field_service.delete(field['id']):
                deleted += 1
        print(f"✓ Deleted {deleted} fields")
    
    def cleanup_fieldsets(self):
        """Delete all fieldsets"""
        print("\n--- Cleaning up Fieldsets ---")
        deleted = 0
        for fieldset in self.fieldset_service.get_all(limit=1000, refresh_cache=True):
            if self.fieldset_service.delete(fieldset['id']):
                deleted += 1
        print(f"✓ Deleted {deleted} fieldsets")
        
    def cleanup_manufacturers(self):
        """Delete all manufacturers"""
        print("\n--- Cleaning up Manufacturers ---")
        deleted = 0
        for manufacturer in self.manufacture_service.get_all(limit=1000, refresh_cache=True):
            if self.manufacture_service.delete(manufacturer['id']):
                deleted += 1
        print(f"✓ Deleted {deleted} manufacturers")
    
    def cleanup_models(self):
        """Delete all models"""
        print("\n--- Cleaning up Models ---")
        deleted = 0
        for model in self.model_service.get_all(limit=1000, refresh_cache=True):
            if self.model_service.delete(model['id']):
                deleted += 1
        print(f"✓ Deleted {deleted} models")
    
    def cleanup_status_labels(self):
        """Delete all status labels"""
        print("\n--- Cleaning up Status Labels ---")
        deleted = 0
        for label in self.status_service.get_all(limit=1000, refresh_cache=True):
            if self.status_service.delete(label['id']):
                deleted += 1
        print(f"✓ Deleted {deleted} status labels")
    
    def cleanup_categories(self):
        """Delete all categories"""
        print("\n--- Cleaning up Categories ---")
        deleted = 0
        for category in self.category_service.get_all(limit=1000, refresh_cache=True):
            if self.category_service.delete(category['id']):
                deleted += 1
        print(f"✓ Deleted {deleted} categories")
    
    def cleanup_locations(self):
        """Delete all locations"""
        print("\n--- Cleaning up Locations ---")
        deleted = 0
        for location in self.location_service.get_all(limit=1000, refresh_cache=True):
            if self.location_service.delete(location['id']):
                deleted += 1
        print(f"✓ Deleted {deleted} locations")
        
    def purge_all(self):
        """
        Purges all soft-deleted records by calling the official Snipe-IT artisan command.
        This should be run AFTER all cleanup operations.
        """
        print("\n--- Purging all deleted ---")
        CrudBaseService.purge_deleted_via_database()
        print(f"✓ Purged all deleted records")
        

def main():
    parser = argparse.ArgumentParser(description='Snipe-IT Setup Tool')
    parser.add_argument('action', 
                        choices=['setup', 'cleanup', 'reset'],
                        nargs='?', 
                        default='reset',
                        help='Action to perform (defaults to "reset")')
    args = parser.parse_args()
    
    setup = SnipeITSetup()
    
    if args.action == 'setup':
        # To prevent issues, a setup should always start from a clean slate.
        # We will run the same logic as 'reset'.
        print("INFO: 'setup' action runs a full reset to ensure a clean environment.")
        setup.cleanup_all()
        setup.purge_all()
        setup.setup_all()
    elif args.action == 'cleanup':
        setup.cleanup_all()
    elif args.action == 'reset':
        setup.cleanup_all()
        setup.purge_all()
        print("\n" + "=" * 60)
        print("Waiting before setup...")
        print("=" * 60)
        time.sleep(3)
        setup.setup_all()

if __name__ == "__main__":
    main()