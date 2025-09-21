from api_client import make_api_request
from config import SNIPE_URL, HEADERS, VERIFY_SSL
from schema import CUSTOM_FIELDS
                        
def get_all():
    response = make_api_request("GET", "/api/v1/fields", params={"limit": 5000})
    if response and response.ok:
        return response.json().get("rows", [])
    return []

def get_by_id(field_id):
    response = make_api_request("GET", f"/api/v1/fields/{field_id}")
    if response and response.ok:
        return response.json()
    return None

def get_by_name(name):
    fields = get_all()
    for field in fields:
        if field.get("name") == name:
            return field
    return None

def create(field_data):
    response = make_api_request("POST", "/api/v1/fields", json=field_data)
    if response and response.ok:
        return response.json()
    elif response:
        print(f"Failed to create field: {response.text}")
    return None

def update(field_id, field_data):
    response = make_api_request("PUT", f"/api/v1/fields/{field_id}", json=field_data)
    if response and response.ok:
        return response.json()
    return None

def delete_by_id(field_id):
    response = make_api_request("DELETE", f"/api/v1/fields/{field_id}")
    return response and response.ok

def delete_all():
    fields = get_all()
    deleted_count = 0
    failed_count = 0
    
    print(f"Found {len(fields)} custom fields to delete...")
    
    for field in fields:
        field_id = field.get("id")
        field_name = field.get("name")
        
        if delete_by_id(field_id):
            print(f"  ✓ Deleted: {field_name} (ID: {field_id})")
            deleted_count += 1
        else:
            print(f"  ✗ Failed to delete: {field_name} (ID: {field_id})")
            failed_count += 1
    
    print(f"Deletion complete: {deleted_count} deleted, {failed_count} failed")
    return deleted_count, failed_count

def create_all_from_config():
    existing_fields = {f["name"]: f["id"] for f in get_all()}
    created_count = 0
    skipped_count = 0
    
    for field_key, field_data in CUSTOM_FIELDS.items():
        if field_data["name"] in existing_fields:
            print(f"  → Field '{field_data['name']}' already exists. Skipping.")
            skipped_count += 1
            continue
            
        print(f"  Creating field: {field_data['name']}...")
        if create(field_data):
            created_count += 1
            print(f"    ✓ Created successfully")
        else:
            print(f"    ✗ Failed to create")
    
    print(f"Creation complete: {created_count} created, {skipped_count} skipped")
    return created_count, skipped_count

def associate_to_fieldset(field_id, fieldset_id):
    response = make_api_request(
        "POST",
        f"/api/v1/fields/{field_id}/associate",
        json={"fieldset_id": fieldset_id}
    )
    return response and response.ok

def disassociate_from_fieldset(field_id, fieldset_id):
    response = make_api_request(
        "POST",
        f"/api/v1/fields/{field_id}/disassociate",
        json={"fieldset_id": fieldset_id}
    )
    return response and response.ok