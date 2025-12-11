import os
import sys
import urllib3
import json
import time
import requests

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.snipe_config import SNIPE_URL, HEADERS, VERIFY_SSL

# To suppress unverified HTTPS requests - Only when self-signed certs are used.
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def make_api_request(method, endpoint, max_retries=3, **kwargs):
    """
    Make API request with retry logic
    Args:
        method: HTTP method (GET, POST, PUT, DELETE)
        endpoint: API endpoint (e.g., "/api/v1/fields")
        max_retries: Number of retries for failed requests
        **kwargs: Additional arguments for requests
    """
    
    url = f"{SNIPE_URL}{endpoint}" if not endpoint.startswith(SNIPE_URL) else endpoint
    
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