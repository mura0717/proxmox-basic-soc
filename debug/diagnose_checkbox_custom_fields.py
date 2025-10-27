#!/usr/bin/env python3
"""Diagnose checkbox field configuration in Snipe-IT"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from crud.fields import FieldService

# The problematic checkbox fields
CHECKBOX_FIELDS = [
    'Intune Managed',
    'Intune Registered',
    'Encrypted',
    'Supervised',
    'EAS Activated',
    'Jailbroken/Rooted',
    'Azure AD Registered',
    'Require User Enrollment Approval',
    'Needs Security Investigation'
]

field_service = FieldService()
all_fields = field_service.get_all(refresh_cache=True)

print("="*80)
print("CHECKBOX FIELDS DIAGNOSIS")
print("="*80)

for field in all_fields:
    if field.get('name') in CHECKBOX_FIELDS:
        print(f"\n{'─'*80}")
        print(f"Field Name: {field.get('name')}")
        print(f"  DB Column: {field.get('db_column_name')}")
        print(f"  Element: {field.get('element')}")
        print(f"  Format: {field.get('format')}")
        print(f"  Field Values: '{field.get('field_values')}'")
        print(f"  Field Encrypted: {field.get('field_encrypted')}")
        
        # The problem diagnosis
        if field.get('format') != 'BOOLEAN':
            print(f"  ⚠️  PROBLEM: Format is '{field.get('format')}', should be 'BOOLEAN'")
        
        if field.get('field_values') and field.get('field_values').strip():
            print(f"  ⚠️  PROBLEM: Field has restricted values: '{field.get('field_values')}'")
            print(f"       This will cause 'invalid options' error!")
        
        if field.get('format') == 'BOOLEAN' and not (field.get('field_values') or '').strip():
            print(f"  ✓ Field is correctly configured")

print("\n" + "="*80)