import os
import requests
from dotenv import load_dotenv
import urllib3
import json
import time

# Suppress InsecureRequestWarning from urllib3 - unverified HTTPS requests 
# Only for testing when self-signed certs are used.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

config_path = "/opt/snipeit-sync/snipe-it-asset-management/.env"
load_dotenv(dotenv_path=config_path)

SNIPE_URL = (os.getenv("SNIPE_URL") or "").rstrip("/")
SNIPE_API_TOKEN = os.getenv("SNIPE_API_TOKEN")

# URL & API TOKEN debug  
#print(f"Loaded Snipe URL: {SNIPE_URL}")
#print(f"Loaded Snipe API TOKEN: {SNIPE_API_TOKEN}")

if not SNIPE_URL or not SNIPE_API_TOKEN:
    raise RuntimeError("SNIPE_URL and SNIPE_API_TOKEN must be set.")

HEADERS = {
    "Authorization": f"Bearer {SNIPE_API_TOKEN}",
    "Accept": "application/json",
    "Content-Type": "application/json", 
}

VERIFY_SSL = False # Set to True in production if using valid certs

# Define ALL unique fields that will be needed across ALL fieldsets


def make_api_request(method, url, max_retries=3, **kwargs):
    # Helper function to make API requests with retry logic
    for attempt in range(max_retries+1): # +1 to include initial attempt
        try:
            response = requests.request(method, url, headers=HEADERS, verify=VERIFY_SSL, **kwargs)
            if response.status_code == 429:
                if attempt < max_retries:
                    try:
                        error_data = response.json()
                        retry_after = int(error_data.get("retryAfter", 15)) + 1
                    except (ValueError, json.JSONDecodeError):
                        retry_after = 15 # Default if parsing fails
                    print(f"-> Rate limited on {method} {url}. Retrying in {retry_after}s... (Attempt {attempt+1}/{max_retries})")
                    time.sleep(retry_after)
                    continue
                else:
                    print(f"-> Max retries exceeded for {method} {url}. Aborting this request.")
                    response.raise_for_status() # Raise the final 429 error

            # For any other non-successful status code, raise an exception
            response.raise_for_status()
            
            return response

        except requests.exceptions.RequestException as e:
            if attempt < max_retries:
                print(f"-> Network error ({e}). Retrying in 10s... (Attempt {attempt+1}/{max_retries})")
                time.sleep(10)
            else:
                print(f"-> A persistent network error occurred. Aborting.")
                raise e
    return None
                        
def get_allfields_map():
    """Fetches all fields from Snipe-IT. Now automatically robust."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/fields", params={"limit": 5000})
    return {field['name']: int(field['id']) for field in response.json().get("rows", [])} if response else {}

def get_allfieldsets_map():
    """Fetches all fieldsets from Snipe-IT. Now automatically robust."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/fieldsets", params={"limit": 5000})
    return {fs['name']: int(fs['id']) for fs in response.json().get("rows", [])} if response else {}

def get_fieldset_fields(fieldset_id):
    """Fetch fields currently associated with a fieldset."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/fieldsets/{fieldset_id}/fields")
    if response:
        return {field['id'] for field in response.json().get("rows", [])}
    return set()

def get_status_labels_map():
    """Fetches all status labels from Snipe-IT."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/statuslabels", params={"limit": 5000})
    return {label['name']: label['id'] for label in response.json().get("rows", [])} if response else {}

def get_categories_map():
    """Fetches all categories from Snipe-IT."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/categories", params={"limit": 5000})
    return {cat['name']: cat['id'] for cat in response.json().get("rows", [])} if response else {}
            
def get_location_map():
    """Fetches all locations from Snipe-IT."""
    response = make_api_request("GET", f"{SNIPE_URL}/api/v1/locations", params={"limit": 5000})
    return {loc['name']: loc['id'] for loc in response.json().get("rows", [])} if response else {}

def create_all_fields():
    """Creates all defined custom fields if they don't already exist."""
    print("\n--- Creating Custom Fields ---")
    existing_fields = set(get_allfields_map().keys())

    for field_data in CUSTOM_FIELDS.values():
        if field_data["name"] in existing_fields:
            print(f"Field '{field_data['name']}' already exists. Skipping.") # Uncomment for less output
            continue
        print(f"Creating field: {field_data['name']}...")
        make_api_request("POST", f"{SNIPE_URL}/api/v1/fields", json=field_data)
    print("Custom field creation process complete.")

def create_all_fieldsets():
    """Creates all defined fieldsets if they don't already exist."""
    print("\n--- Creating Fieldsets ---")
    existing_fieldsets = set(get_allfieldsets_map().keys())
    
    for name in CUSTOM_FIELDSETS.keys():
        if name in existing_fieldsets:
            print(f"Fieldset '{name}' already exists. Skipping.")
            continue
        
        print(f"Creating fieldset: {name}...")
        make_api_request("POST", f"{SNIPE_URL}/api/v1/fieldsets", json={"name": name})
    print("Fieldset creation process complete.")
            
def associate_fields_to_fieldsets():
    """Associates all defined fields with their respective fieldsets."""
    print("\n--- Associating Fields with Fieldsets ---")

    all_fields_map = get_allfields_map()
    all_fieldsets_map = get_allfieldsets_map()

    if not all_fields_map or not all_fieldsets_map:
        print("ERROR: Could not get field and/or fieldset maps. Aborting association.")
        return

    for fs_name, field_keys in CUSTOM_FIELDSETS.items():
        fieldset_id = all_fieldsets_map.get(fs_name)
        
        if not fieldset_id:
            print(f"WARNING: Fieldset '{fs_name}' was not found on the server. Skipping association for it.")
            continue
        
        #existing_field_ids_in_fieldset = get_fieldset_fields(fieldset_id)
    
        print(f"Processing associations for fieldset '{fs_name}' (ID: {fieldset_id})...")
        
        for key in field_keys:
            field_def = CUSTOM_FIELDS.get(key, {})
            field_name = field_def['name']
            field_id = all_fields_map.get(field_name)

            if not field_id:
                print(f"  - WARNING: Could not find a field named '{field_name}' (key: '{key}'). Skipping.")
                continue
            
            """ if field_id in existing_field_ids_in_fieldset:
                print(f"    → Field '{field_name}' already associated. Skipping.")
                continue """
            
            payload = {
                 "fieldset_id": fieldset_id
            }

            print(f"  - Associating field '{field_name}' (ID: {field_id}) to fieldset '{fs_name}'")
            response = make_api_request(
                "POST",
                f"{SNIPE_URL}/api/v1/fields/{field_id}/associate",
                json=payload
            )
            
            if response.ok:
                    print("    ✓ Successfully associated.")
            else:
                    # Handle “already associated” gracefully
                try:
                    data = response.json()
                except Exception:
                    data = {"messages": response.text}
                    msg = str(data).lower()
                    if response.status_code in (409, 422) and ("already" in msg or "exists" in msg):
                        print("    → Already associated. Skipping.")
                    else:
                        response.raise_for_status()
                except Exception as e:
                    print(f"    ✗ Failed to associate: {e}")

    print("Field association process complete.")
    
def create_status_labels():
    """Creates status labels if they don't already exist."""
    print("\n--- Creating Status Labels ---")
    existing_labels = set(get_status_labels_map().keys())

    for label_name, config in STATUS_LABELS.items():
        if label_name in existing_labels:
            print(f"Status label '{label_name}' already exists. Skipping.") 
            continue
        print(f"Creating status label: {label_name}...")
        payload = {
            "name": label_name,
            "color": config.get("color", "#FFFFFF"),
            "type": config.get("type", "deployable"),
            "show_in_nav": config.get("show_in_nav", False),
            "default_label": config.get("default_label", False)
        }
        make_api_request("POST", f"{SNIPE_URL}/api/v1/statuslabels", json=payload)
    print("Status label creation process complete.")

def create_categories():
    """Creates categories if they don't already exist."""
    print("\n--- Creating Categories ---")
    existing_categories = set(get_categories_map().keys())

    for category_name, config in CATEGORIES.items():
        if category_name in existing_categories:
            print(f"Category '{category_name}' already exists. Skipping.") 
            continue
        print(f"Creating category: {category_name}...")
        payload = {
            "name": category_name,
            "category_type": config.get("category_type", "asset"),
            "use_default_eula": config.get("use_default_eula", False),
            "require_acceptance": config.get("require_acceptance", False),
            "checkin_email": config.get("checkin_email", False)
        }
        make_api_request("POST", f"{SNIPE_URL}/api/v1/categories", json=payload)
    print("Category creation process complete.")

def create_locations():
    """Creates locations if they don't already exist."""
    print("\n--- Creating Locations ---")
    existing_locations = set(get_location_map().keys())
    for location_name in LOCATIONS:
        if location_name in existing_locations:
            print(f"Location '{location_name}' already exists. Skipping.") 
            continue
        print(f"Creating location: {location_name}...")
        payload = {
            "name": location_name,
        }
        make_api_request("POST", f"{SNIPE_URL}/api/v1/locations", json=payload)
    print("Location creation process complete.")

# Optional: Functions to delete all created
def delete_all_fields():
    """Deletes all custom fields defined in CUSTOM FIELDS."""
    print("--- Deleting Custom Fields ---")
    existing_fields = get_allfields_map()
    for field_def in CUSTOM_FIELDS.values():
        field_name = field_def["name"]
        if field_name not in existing_fields:
            print(f"Field '{field_name}' does not exist. Skipping.")
            continue
        field_id = existing_fields[field_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/fields/{field_id}")
        print(f"Deleted field: {field_name} (ID: {field_id})")          
            
def delete_all_fieldsets():
    """Deletes all fieldsets defined in CUSTOM FIELDSETS."""
    print("\n--- Deleting Fieldsets ---")
    existing_fieldsets = get_allfieldsets_map()
    
    if not existing_fieldsets:
        print("No fieldsets found on server.")
        return
    
    for fieldset_name in CUSTOM_FIELDSETS.keys():
        if fieldset_name not in existing_fieldsets:
            print(f"Fieldset '{fieldset_name}' does not exist. Skipping.")
            continue
        fieldset_id = int(existing_fieldsets[fieldset_name])
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/fieldsets/{fieldset_id}")
        print(f"Deleted fieldset: {fieldset_name} (ID: {fieldset_id})")

def delete_all_status_labels():
    """Deletes all status labels defined in STATUS_LABELS."""
    print("\n--- Deleting Status Labels ---")
    existing_labels = get_status_labels_map()
    for label_name in STATUS_LABELS.keys():
        if label_name not in existing_labels:
            print(f"Status label '{label_name}' does not exist. Skipping.")
            continue
        label_id = existing_labels[label_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/statuslabels/{label_id}")
        print(f"Deleted status label: {label_name} (ID: {label_id})")
        
def delete_all_categories():
    """Deletes all categories defined in CATEGORIES."""
    print("\n--- Deleting Categories ---")
    existing_categories = get_categories_map()
    for category_name in CATEGORIES.keys():
        if category_name not in existing_categories:
            print(f"Category '{category_name}' does not exist. Skipping.")
            continue
        category_id = existing_categories[category_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/categories/{category_id}")
        print(f"Deleted category: {category_name} (ID: {category_id})")

def delete_all_locations():
    """Deletes all locations defined in LOCATIONS."""
    print("\n--- Deleting Locations ---")
    existing_locations = get_location_map()
    for location_name in LOCATIONS:
        if location_name not in existing_locations:
            print(f"Location '{location_name}' does not exist. Skipping.")
            continue
        location_id = existing_locations[location_name]
        make_api_request("DELETE", f"{SNIPE_URL}/api/v1/locations/{location_id}")
        print(f"Deleted location: {location_name} (ID: {location_id})")

if __name__ == "__main__":
    """DELETE ALL CREATED"""
    delete_all_fieldsets()
    delete_all_fields()
    delete_all_status_labels()
    delete_all_categories()
    delete_all_locations()
    
    """CREATE ALL"""
    #create_status_labels()
    #create_categories()
    #create_locations()
    #create_all_fields()
    #create_all_fieldsets()
    #associate_fields_to_fieldsets()
    
   