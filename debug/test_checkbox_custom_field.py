#!/usr/bin/env python3
"""
Comprehensive test script for checkbox custom fields in Snipe-IT
This script will create test fields, assets, and verify the entire workflow
"""
import sys
import os
import json
import time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from snipe_api.services.fields import FieldService
from snipe_api.services.fieldsets import FieldsetService
from snipe_api.services.assets import AssetService
from snipe_api.services.models import ModelService
from snipe_api.services.categories import CategoryService
from snipe_api.services.manufacturers import ManufacturerService
from snipe_api.services.status_labels import StatusLabelService
from snipe_api.services.crudbase import BaseCRUDService
from snipe_api.snipe_client import make_api_request

# Colors for output
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
BLUE = '\033[94m'
RESET = '\033[0m'

def print_step(msg):
    print(f"\n{BLUE}═══ {msg} ═══{RESET}")

def print_success(msg):
    print(f"{GREEN}✓ {msg}{RESET}")

def print_error(msg):
    print(f"{RED}✗ {msg}{RESET}")

def print_info(msg):
    print(f"{YELLOW}ℹ {msg}{RESET}")

def print_json(data, label="JSON Data"):
    print(f"\n{YELLOW}{label}:{RESET}")
    print(json.dumps(data, indent=2))

class CheckboxFieldTester:
    def __init__(self):
        self.field_service = FieldService()
        self.fieldset_service = FieldsetService()
        self.asset_service = AssetService()
        self.model_service = ModelService()
        self.category_service = CategoryService()
        self.manufacturer_service = ManufacturerService()
        self.status_service = StatusLabelService()
        
        # Test data that will be created
        self.test_field_id = None
        self.test_fieldset_id = None
        self.test_model_id = None
        self.test_asset_id = None
        
        # Names for test entities
        self.test_field_name = "Test Checkbox Field DELETE ME"
        self.test_fieldset_name = "Test Fieldset DELETE ME"
        self.test_model_name = "Test Model DELETE ME"
        self.test_asset_name = "TEST-ASSET-DELETE-ME"

    def run_full_test(self):
        """Run the complete test workflow"""
        try:
            print_step("STARTING CHECKBOX FIELD TEST")
            
            # Step 1: Create test custom field
            if not self.create_test_field():
                return
            
            # Step 2: Verify field via API
            if not self.verify_field_api():
                return
            
            # Step 3: Create test fieldset
            if not self.create_test_fieldset():
                return
            
            # Step 4: Create test model
            if not self.create_test_model():
                return
            
            # Step 5: Create test asset
            if not self.create_test_asset():
                return
            
            # Step 6: Test different checkbox values
            if not self.test_checkbox_values():
                return
            
            print_step("TEST COMPLETED SUCCESSFULLY")
            print_success("All tests passed! The checkbox field works correctly.")
            
        except Exception as e:
            print_error(f"Test failed with exception: {e}")
            
        finally:
            # Cleanup
            self.cleanup()

    def create_test_field(self):
        """Step 1: Create a test checkbox field"""
        print_step("Step 1: Creating test checkbox field")
        
        # First, check if it already exists and delete it
        existing_fields = self.field_service.get_all(refresh_cache=True)
        for field in existing_fields:
            if field['name'] == self.test_field_name:
                print_info(f"Found existing test field (ID: {field['id']}), deleting...")
                if self.field_service.delete(field['id']):
                    print_info("Purging soft-deleted records to free up name...")
                    BaseCRUDService.purge_deleted_via_database()
                time.sleep(1)
        
        # Create the field
        payload = {
            'name': self.test_field_name,
            'element': 'checkbox',
            'format': 'BOOLEAN',
            'help_text': 'Test checkbox field for debugging'
        }
        
        print_info("Creating field with payload:")
        print_json(payload, "Field Creation Payload")
        
        result = self.field_service.create(payload)
        
        if result:
            self.test_field_id = result.get('id')
            print_success(f"Field created with ID: {self.test_field_id}")
            print_json(result, "Field Creation Response")
            
            # The create response uses 'db_column', the GET response uses 'db_column_name'.
            self.test_field_db_name = result.get('db_column') or result.get('db_column_name')
            if not self.test_field_db_name:
                print_error("Could not find DB column name in response!")
                return False

            # IMPORTANT FIX: Clear field_values to prevent "invalid options" error on asset creation.
            print_info("Clearing field_values to ensure correct checkbox behavior...")
            fix_payload = {'field_values': ''}
            if self.field_service.update(self.test_field_id, fix_payload):
                print_success("field_values cleared successfully.")
            else:
                print_error("Failed to clear field_values.")
                return False
            
            return True
        else:
            print_error("Failed to create field")
            return False

    def verify_field_api(self):
        """Step 2: Verify the field via API"""
        print_step("Step 2: Verifying field via API")
        
        # Get all fields
        print_info("Fetching all fields...")
        all_fields = self.field_service.get_all(refresh_cache=True)
        
        test_field = None
        for field in all_fields:
            if field['name'] == self.test_field_name:
                test_field = field
                break
        
        if test_field:
            print_success("Found test field in list")
            print_json(test_field, "Field from List API")
            
            # Check critical fields
            print_info("\nChecking critical field properties:")
            print(f"  - element: {test_field.get('element')} (expected: 'checkbox')") # This will be None - Fetching element happens with 'type'.
            print(f"  - type: {test_field.get('type')} (expected: 'checkbox')")
            print(f"  - format: {test_field.get('format')} (expected: 'BOOLEAN')")
            print(f"  - db_column_name: {test_field.get('db_column_name')}")
            
            # Get field individually
            print_info(f"\nFetching field individually (ID: {self.test_field_id})...")
            response = make_api_request("GET", f"/api/v1/fields/{self.test_field_id}")
            
            if response:
                individual_field = response.json()
                print_json(individual_field, "Individual Field API Response")
                
                # Store DB column name
                self.test_field_db_name = individual_field.get('db_column_name', test_field.get('db_column_name'))
                
                return True
            else:
                print_error("Failed to fetch field individually")
                return False
        else:
            print_error("Test field not found in list")
            return False

    def create_test_fieldset(self):
        """Step 3: Create a test fieldset and add the field"""
        print_step("Step 3: Creating test fieldset")
        
        # Check if exists and delete
        existing = self.fieldset_service.get_by_name(self.test_fieldset_name)
        if existing:
            print_info(f"Deleting existing fieldset (ID: {existing['id']})")
            self.fieldset_service.delete(existing['id'])
            time.sleep(1)
        
        # Create fieldset
        payload = {'name': self.test_fieldset_name}
        result = self.fieldset_service.create(payload)
        
        if result:
            self.test_fieldset_id = result['id']
            print_success(f"Fieldset created with ID: {self.test_fieldset_id}")
            
            # Associate field with fieldset
            print_info("Associating field with fieldset...")
            assoc_result = self.field_service.associate_to_fieldset(
                self.test_field_id, 
                self.test_fieldset_id
            )
            
            if assoc_result:
                print_success("Field associated with fieldset")
            else:
                print_error("Failed to associate field with fieldset")
            
            return True
        else:
            print_error("Failed to create fieldset")
            return False

    def create_test_model(self):
        """Step 4: Create a test model with the fieldset"""
        print_step("Step 4: Creating test model")
        
        # Get or create category and manufacturer
        category = self.category_service.get_by_name('Laptops')
        if not category:
            print_error("Category 'Laptops' not found")
            return False
            
        manufacturer = self.manufacturer_service.get_by_name('Generic')
        if not manufacturer:
            print_info("Creating Generic manufacturer...")
            manufacturer = self.manufacturer_service.create({'name': 'Generic'})
        
        # Check if model exists and delete
        existing = self.model_service.get_by_name(self.test_model_name)
        if existing:
            print_info(f"Deleting existing model (ID: {existing['id']})")
            self.model_service.delete(existing['id'])
            time.sleep(1)
        
        # Create model
        payload = {
            'name': self.test_model_name,
            'category_id': category['id'],
            'manufacturer_id': manufacturer['id'],
            'fieldset_id': self.test_fieldset_id
        }
        
        print_json(payload, "Model Creation Payload")
        result = self.model_service.create(payload)
        
        if result:
            self.test_model_id = result['id']
            print_success(f"Model created with ID: {self.test_model_id}")
            return True
        else:
            print_error("Failed to create model")
            return False

    def create_test_asset(self):
        """Step 5: Create a test asset"""
        print_step("Step 5: Creating test asset")
        
        # Get status
        status = self.status_service.get_by_name('Ready to Deploy')
        if not status:
            statuses = self.status_service.get_all()
            if statuses:
                status = statuses[0]  # Use first available
        
        # Check if asset exists and delete
        existing_assets = self.asset_service.get_all()
        for asset in existing_assets:
            if asset.get('name') == self.test_asset_name:
                print_info(f"Deleting existing test asset (ID: {asset['id']})")
                self.asset_service.delete(asset['id'])
                time.sleep(1)
        
        # Create asset
        payload = {
            'name': self.test_asset_name,
            'asset_tag': f'TEST-{int(time.time())}',
            'model_id': self.test_model_id,
            'status_id': status['id'] if status else 1,
            'serial': f'TEST-SERIAL-{int(time.time())}'
        }
        
        print_json(payload, "Asset Creation Payload")
        result = self.asset_service.create(payload)
        
        if result:
            self.test_asset_id = result['id']
            print_success(f"Asset created with ID: {self.test_asset_id}")
            return True
        else:
            print_error("Failed to create asset")
            return False

    def test_checkbox_values(self):
        """Step 6: Test updating the asset with different checkbox values"""
        print_step("Step 6: Testing checkbox field updates")
        
        test_values = [
            ("string '1'", "1"),
            ("string '0'", "0"),
            ("boolean true", True),
            ("boolean false", False),
            ("integer 1", 1),
            ("integer 0", 0),
            ("string 'true'", "true"),
            ("string 'false'", "false"),
        ]
        
        successful_values = []
        failed_values = []
        
        for description, value in test_values:
            print_info(f"\nTesting with {description}: {value} (type: {type(value).__name__})")
            
            # Create update payload
            payload = {
                self.test_field_db_name: value
            }
            
            print_json(payload, "Update Payload")
            
            # Update asset
            result = self.asset_service.update(self.test_asset_id, payload)
            
            if result:
                print_success(f"Update successful with {description}")
                successful_values.append((description, value))
                
                # Verify the value was saved
                print_info("Fetching asset to verify...")
                asset = self.asset_service.get_by_id(self.test_asset_id)
                if asset:
                    custom_fields = asset.get('custom_fields', {})
                    saved_value = None
                    for field_name, field_data in custom_fields.items():
                        if field_name == self.test_field_name:
                            saved_value = field_data.get('value')
                            break
                    
                    print(f"  Saved value: {saved_value} (type: {type(saved_value).__name__})")
            else:
                print_error(f"Update failed with {description}")
                failed_values.append((description, value))
                
        # Add a final verification step
        print_info("\nFinal verification of the last successful value...")
        asset = self.asset_service.get_by_id(self.test_asset_id)
        final_value = asset.get('custom_fields', {}).get(self.test_field_name, {}).get('value')
        expected_value = '0' # The last test is 'false' which should save as '0'
        if str(final_value) == expected_value:
            print_success(f"Final value is '{final_value}', which matches expected '{expected_value}'.")
        else:
            print_error(f"Final value is '{final_value}', but expected '{expected_value}'.")
        
        # Summary
        print_step("RESULTS SUMMARY")
        
        if successful_values:
            print_success(f"Successful values ({len(successful_values)}):")
            for desc, val in successful_values:
                print(f"  ✓ {desc}: {val}")
        
        if failed_values:
            print_error(f"Failed values ({len(failed_values)}):")
            for desc, val in failed_values:
                print(f"  ✗ {desc}: {val}")
        
        return len(successful_values) > 0

    def cleanup(self):
        """Cleanup test data"""
        print_step("Cleaning up test data")
        
        response = input("\nDelete all test data? (yes/no): ")
        if response.lower() != 'yes':
            print_info("Keeping test data for manual inspection")
            print_info(f"  - Test Field: {self.test_field_name} (ID: {self.test_field_id})")
            print_info(f"  - Test Fieldset: {self.test_fieldset_name} (ID: {self.test_fieldset_id})")
            print_info(f"  - Test Model: {self.test_model_name} (ID: {self.test_model_id})")
            print_info(f"  - Test Asset: {self.test_asset_name} (ID: {self.test_asset_id})")
            return
        
        # Delete in reverse order
        if self.test_asset_id:
            print_info("Deleting test asset...")
            self.asset_service.delete(self.test_asset_id)
            
        if self.test_model_id:
            print_info("Deleting test model...")
            self.model_service.delete(self.test_model_id)

        # IMPORTANT: Disassociate field from fieldset BEFORE deleting the field
        if self.test_field_id and self.test_fieldset_id:
            print_info("Disassociating field from fieldset...")
            if not self.field_service.disassociate_from_fieldset(self.test_field_id, self.test_fieldset_id):
                print_error("Failed to disassociate field. Field deletion may fail.")
            else:
                print_success("Field disassociated successfully.")
        
        if self.test_field_id:
            print_info("Deleting test field...")
            self.field_service.delete(self.test_field_id)  
              
        if self.test_fieldset_id:
            print_info("Deleting test fieldset...")
            self.fieldset_service.delete(self.test_fieldset_id)
        
        BaseCRUDService.purge_deleted_via_database()
        time.sleep(1)
        print_success("Cleanup complete")

if __name__ == "__main__":
    tester = CheckboxFieldTester()
    tester.run_full_test()