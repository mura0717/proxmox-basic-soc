#!/usr/bin/env python3
"""
Intune Integration for Snipe-IT
Syncs assets from Microsoft Intune to Snipe-IT
"""

import os
import sys
import requests
import json
from datetime import datetime, timezone
from typing import Dict, List, Optional
from msal import ConfidentialClientApplication

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets_sync_library.asset_matcher import AssetMatcher
from debug.asset_debug_logger import debug_logger 
from config.microsoft365_config import Microsoft365 
from debug.intune_categorize_from_logs import intune_debug_categorization 
from utils.mac_utils import combine_macs, normalize_mac

class IntuneSync:
    """Microsoft Intune synchronization service"""
    
    def __init__(self):
        self.asset_matcher = AssetMatcher()
        self.graph_url = "https://graph.microsoft.com/v1.0"
        self.microsoft365 = Microsoft365() # Instantiate the Microsoft365 helper
    
    def get_access_token(self) -> Optional[str]:
        """Ensure a valid access token is available and return it."""
        if not self.microsoft365.access_token:
            if not self.microsoft365.authenticate():
                print("Authentication failed via Microsoft365 helper.")
                return None
        return self.microsoft365.access_token
    
    def get_intune_assets(self) -> List[Dict]:
        """Fetch all managed assets from Intune"""
        # Ensure we have an access token before making the request
        access_token = self.get_access_token()
        if not access_token:
            print("No access token available, cannot fetch Intune assets.")
            return []
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        assets = []
        url = f"{self.graph_url}/deviceManagement/managedDevices"
        
        while url:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                if not data.get('value'):
                    print(f"DEBUG: API call to {url} returned an empty 'value' array.") # Keep this for immediate feedback
                    print(f"DEBUG: Full API Response: {json.dumps(data, indent=2)}")
                
                assets.extend(data.get('value', []))
                url = data.get('@odata.nextLink')  # Handle pagination
                
            except requests.exceptions.RequestException as e:
                if 'response' in locals() and response is not None:
                    print(f"Intune API Error - Response Status Code: {response.status_code}")
                    print(f"Intune API Error - Response Body: {response.text}")
                print(f"Error fetching assets: {e}")
                break
        
        return assets
    
    def _combine_mac_addresses(self, asset: Dict) -> str:
        """Combine all MAC addresses into a single field"""
        macs = []
        if asset.get('wiFiMacAddress'): 
            macs.append(normalize_mac(asset['wiFiMacAddress']))
        if asset.get('ethernetMacAddress'): 
            macs.append(normalize_mac(asset['ethernetMacAddress']))
        return combine_macs(macs)
    
    def transform_intune_to_snipeit(self, intune_asset: Dict) -> Dict:
        """Transform Intune asset data to Snipe-IT format"""
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Map Intune fields to Snipe-IT custom fields
        transformed = {
            # Identity
            'name': intune_asset.get('deviceName'),
            'serial': intune_asset.get('serialNumber'),
            'azure_ad_id': intune_asset.get('azureADDeviceId'),
            'intune_device_id': intune_asset.get('id'),
            'device_enrollment_type': intune_asset.get('deviceEnrollmentType'),
            'device_registration_state': intune_asset.get('deviceRegistrationState'),
            'device_category_display_name': intune_asset.get('deviceCategoryDisplayName'),
            'udid': intune_asset.get('udid'),
            
            # Management
            'intune_managed': True,
            'intune_registered': intune_asset.get('azureADRegistered', False),
            'intune_enrollment_date': intune_asset.get('enrolledDateTime'),
            'intune_last_sync': intune_asset.get('lastSyncDateTime'),
            'managed_by': intune_asset.get('managementAgent'),
            'intune_category': intune_asset.get('deviceCategoryDisplayName'),
            'ownership': intune_asset.get('managedDeviceOwnerType'),
            'device_state': intune_asset.get('deviceRegistrationState'),
            'intune_compliance': intune_asset.get('complianceState'),
            'compliance_grace_expiration': intune_asset.get('complianceGracePeriodExpirationDateTime'),
            'management_cert_expiration': intune_asset.get('managementCertificateExpirationDate'),
            'enrollment_profile_name': intune_asset.get('enrollmentProfileName'),
            'require_user_enrollment_approval': intune_asset.get('requireUserEnrollmentApproval'),
            'activation_lock_bypass_code': intune_asset.get('activationLockBypassCode'),
            'last_update_source': 'intune',
            'last_update_at': current_time,
            
            # OS Information
            'os_platform': intune_asset.get('operatingSystem'),
            'os_version': intune_asset.get('osVersion'),
            'sku_family': intune_asset.get('skuFamily'),
            'join_type': intune_asset.get('deviceEnrollmentType'),
            'product_name': intune_asset.get('model'),
            'android_security_patch_level': intune_asset.get('androidSecurityPatchLevel'),
            
            # Hardware
            'manufacturer': intune_asset.get('manufacturer'),
            'model': intune_asset.get('model'),
            'total_storage': intune_asset.get('totalStorageSpaceInBytes'),
            'free_storage': intune_asset.get('freeStorageSpaceInBytes'),
            'processor_architecture': intune_asset.get('processorArchitecture'),
            'physical_memory_in_bytes': intune_asset.get('physicalMemoryInBytes'),
            
            # User
            'primary_user_upn': intune_asset.get('userPrincipalName'),
            'primary_user_email': intune_asset.get('emailAddress'),
            'primary_user_display_name': intune_asset.get('userDisplayName'),
            'primary_user_id': intune_asset.get('userId'),
            'user_display_name': intune_asset.get('userDisplayName'),
            
            # Network
            'wifi_mac': normalize_mac(intune_asset.get('wiFiMacAddress')),
            'ethernet_mac': normalize_mac(intune_asset.get('ethernetMacAddress')),
            'mac_addresses': self._combine_mac_addresses(intune_asset),
            
            # Mobile specific
            'imei': intune_asset.get('imei'),
            'meid': intune_asset.get('meid'),
            'phone_number': intune_asset.get('phoneNumber'),
            'subscriber_carrier': intune_asset.get('subscriberCarrier'),
            'cellular_technology': intune_asset.get('cellularTechnology'),
            'iccid': intune_asset.get('iccid'),
            
            # Security
            'encrypted': intune_asset.get('isEncrypted', False),
            'supervised': intune_asset.get('isSupervised', False),
            'jailbroken': intune_asset.get('jailBroken', False),
            
            # EAS
            'eas_activated': intune_asset.get('easActivated', False),
            'eas_activation_id': intune_asset.get('easDeviceId'),
            'eas_last_sync': intune_asset.get('exchangeLastSuccessfulSyncDateTime'),
            'exchange_access_state': intune_asset.get('exchangeAccessState'),
            'exchange_access_state_reason': intune_asset.get('exchangeAccessStateReason'),
            'remote_assistance_session_url': intune_asset.get('remoteAssistanceSessionUrl'),
            'remote_assistance_session_error_details': intune_asset.get('remoteAssistanceSessionErrorDetails'),
            
            # Device type determination
            'device_health_attestation_state': intune_asset.get('deviceHealthAttestationState'),
            'partner_reported_threat_state': intune_asset.get('partnerReportedThreatState'),
            'notes': intune_asset.get('notes'),
            
            # Software Inventory
            'configuration_manager_client_enabled_features': intune_asset.get('configurationManagerClientEnabledFeatures'),
            
            # Cloud Resource Information       
            'azure_resource_id': intune_asset.get('azureResourceId'),
            'azure_subscription_id': intune_asset.get('azureSubscriptionId'),
            'azure_resource_group': intune_asset.get('azureResourceGroup'),
            'azure_region': intune_asset.get('azureRegion'),
            'azure_tags_json': intune_asset.get('azureTagsJson'),
        }

        # Remove None values
        return {k: v for k, v in transformed.items() if v is not None and v != ""}

    def sync_to_snipeit(self) -> Dict:
        """Main sync function"""
        print("Starting Intune synchronization...")
        # Authenticate using the Microsoft365 helper
        if not self.microsoft365.authenticate():
            print("Intune sync authentication failed.")
            return {'error': 'Authentication failed'}
        
        self.asset_matcher.clear_all_caches()
        
        # Fetch assets from Intune
        intune_assets = self.get_intune_assets()
        print(f"Found {len(intune_assets)} assets in Intune")
        
        # DEBUG: Log raw Intune API responses
        for asset in intune_assets:
            device_id = asset.get('id', 'unknown')
            debug_logger.log_raw_host_data('intune', device_id, asset)  
            
        # Transform and prepare for Snipe-IT
        transformed_assets = []
        for asset in intune_assets:
            transformed = self.transform_intune_to_snipeit(asset)
            transformed_assets.append(transformed)
        
        # DEBUG: Log transformed data
        debug_logger.log_parsed_asset_data('intune', transformed_assets)
        
        # Send to asset matcher for processing
        results = self.asset_matcher.process_scan_data('intune', transformed_assets)
        
        # DEBUG: Log sync results
        debug_logger.log_sync_summary('intune', results)
        
        print(f"Sync complete: {results['created']} created, {results['updated']} updated, {results['failed']} failed")
        return results

if __name__ == "__main__":
    debug_logger.clear_logs('intune')
    
    if intune_debug_categorization.debug:
        intune_debug_categorization.write_managed_assets_to_logfile()
    else:
        sync = IntuneSync()
        sync.sync_to_snipeit()