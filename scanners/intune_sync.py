#!/usr/bin/env python3
"""
Intune Integration for Snipe-IT
Syncs devices from Microsoft Intune to Snipe-IT
"""

import os
import sys
import requests
import json
from datetime import datetime, timezone
from typing import List, Dict, Optional
from msal import ConfidentialClientApplication


sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from lib.asset_matcher import AssetMatcher
from debug.device_debug_logger import debug_logger

class IntuneSync:
    """Microsoft Intune synchronization service"""
    
    def __init__(self):
        # Load credentials from environment
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Azure credentials not configured in environment")
        
        self.asset_matcher = AssetMatcher()
        self.graph_url = "https://graph.microsoft.com/v1.0"
        self.access_token = None
    
    def authenticate(self) -> bool:
        """Authenticate with Microsoft Graph API"""
        try:
            app = ConfidentialClientApplication(
                self.client_id,
                authority=f"https://login.microsoftonline.com/{self.tenant_id}",
                client_credential=self.client_secret
            )
            
            result = app.acquire_token_silent(
                ["https://graph.microsoft.com/.default"], 
                account=None
            )
            
            if not result:
                result = app.acquire_token_for_client(
                    scopes=["https://graph.microsoft.com/.default"]
                )
            
            if "access_token" in result:
                self.access_token = result["access_token"]
                return True
            else:
                print(f"Authentication failed: {result.get('error_description')}")
                return False
                
        except Exception as e:
            print(f"Authentication error: {e}")
            return False
    
    def get_managed_devices(self) -> List[Dict]:
        """Fetch all managed devices from Intune"""
        if not self.access_token:
            if not self.authenticate():
                return []
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        devices = []
        url = f"{self.graph_url}/deviceManagement/managedDevices"
        
        while url:
            try:
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                devices.extend(data.get('value', []))
                url = data.get('@odata.nextLink')  # Handle pagination
                
            except requests.exceptions.RequestException as e:
                print(f"Error fetching devices: {e}")
                break
        
        return devices
    
    def get_device_details(self, device_id: str) -> Optional[Dict]:
        """Get detailed information for a specific device"""
        if not self.access_token:
            return None
        
        headers = {
            'Authorization': f'Bearer {self.access_token}',
            'Content-Type': 'application/json'
        }
        
        try:
            # Get additional device details
            url = f"{self.graph_url}/deviceManagement/managedDevices/{device_id}"
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            print(f"Error fetching device details for {device_id}: {e}")
            return None
    
    def transform_intune_to_snipeit(self, intune_device: Dict) -> Dict:
        """Transform Intune device data to Snipe-IT format"""
        current_time = datetime.now(timezone.utc).isoformat()
        
        # Map Intune fields to Snipe-IT custom fields
        transformed = {
            # Identity
            'name': intune_device.get('deviceName'),
            'serial': intune_device.get('serialNumber'),
            'azure_ad_id': intune_device.get('azureADDeviceId'),
            'intune_device_id': intune_device.get('id'),
            'device_enrollment_type': intune_device.get('deviceEnrollmentType'),
            'device_registration_state': intune_device.get('deviceRegistrationState'),
            'device_category_display_name': intune_device.get('deviceCategoryDisplayName'),
            'udid': intune_device.get('udid'),
            
            # Management
            'intune_managed': True,
            'intune_registered': intune_device.get('azureADRegistered', False),
            'intune_enrollment_date': intune_device.get('enrolledDateTime'),
            'intune_last_sync': intune_device.get('lastSyncDateTime'),
            'managed_by': intune_device.get('managementAgent'),
            'intune_category': intune_device.get('deviceCategoryDisplayName'),
            'ownership': intune_device.get('managedDeviceOwnerType'),
            'device_state': intune_device.get('deviceRegistrationState'),
            'intune_compliance': intune_device.get('complianceState'),
            'compliance_grace_expiration': intune_device.get('complianceGracePeriodExpirationDateTime'),
            'management_cert_expiration': intune_device.get('managementCertificateExpirationDate'),
            'enrollment_profile_name': intune_device.get('enrollmentProfileName'),
            'require_user_enrollment_approval': intune_device.get('requireUserEnrollmentApproval'),
            'activation_lock_bypass_code': intune_device.get('activationLockBypassCode'),
            'last_update_source': 'intune',
            'last_update_at': current_time,
            
            # OS Information
            'os_platform': intune_device.get('operatingSystem'),
            'os_version': intune_device.get('osVersion'),
            'sku_family': intune_device.get('skuFamily'),
            'join_type': intune_device.get('deviceEnrollmentType'),
            'product_name': intune_device.get('model'),
            'android_security_patch_level': intune_device.get('androidSecurityPatchLevel'),
            
            # Hardware
            'manufacturer': intune_device.get('manufacturer'),
            'model': intune_device.get('model'),
            'total_storage': intune_device.get('totalStorageSpaceInBytes'),
            'free_storage': intune_device.get('freeStorageSpaceInBytes'),
            'processor_architecture': intune_device.get('processorArchitecture'),
            'physical_memory_in_bytes': intune_device.get('physicalMemoryInBytes'),
            
            # User
            'primary_user_upn': intune_device.get('userPrincipalName'),
            'primary_user_email': intune_device.get('emailAddress'),
            'primary_user_display_name': intune_device.get('userDisplayName'),
            'primary_user_id': intune_device.get('userId'),
            'user_display_name': intune_device.get('userDisplayName'),
            
            # Network
            'wifi_mac': intune_device.get('wiFiMacAddress'),
            'ethernet_mac': intune_device.get('ethernetMacAddress'),
            'mac_addresses': self._combine_mac_addresses(intune_device),
            
            # Mobile specific
            'imei': intune_device.get('imei'),
            'meid': intune_device.get('meid'),
            'phone_number': intune_device.get('phoneNumber'),
            'subscriber_carrier': intune_device.get('subscriberCarrier'),
            'cellular_technology': intune_device.get('cellularTechnology'),
            'iccid': intune_device.get('iccid'),
            
            # Security
            'encrypted': intune_device.get('isEncrypted', False),
            'supervised': intune_device.get('isSupervised', False),
            'jailbroken': intune_device.get('jailBroken', False),
            
            # EAS
            'eas_activated': intune_device.get('easActivated', False),
            'eas_activation_id': intune_device.get('easDeviceId'),
            'eas_last_sync': intune_device.get('exchangeLastSuccessfulSyncDateTime'),
            'exchange_access_state': intune_device.get('exchangeAccessState'),
            'exchange_access_state_reason': intune_device.get('exchangeAccessStateReason'),
            'remote_assistance_session_url': intune_device.get('remoteAssistanceSessionUrl'),
            'remote_assistance_session_error_details': intune_device.get('remoteAssistanceSessionErrorDetails'),
            
            # Device type determination
            'device_health_attestation_state': intune_device.get('deviceHealthAttestationState'),
            'partner_reported_threat_state': intune_device.get('partnerReportedThreatState'),
            'notes': intune_device.get('notes'),
            
            # Software Inventory
            'configuration_manager_client_enabled_features': intune_device.get('configurationManagerClientEnabledFeatures'),
            
            # Cloud Resource Information       
            'azure_resource_id': intune_device.get('azureResourceId'),
            'azure_subscription_id': intune_device.get('azureSubscriptionId'),
            'azure_resource_group': intune_device.get('azureResourceGroup'),
            'azure_region': intune_device.get('azureRegion'),
            'azure_tags_json': intune_device.get('azureTagsJson'),
        }

        # Remove None values
        return {k: v for k, v in transformed.items() if v is not None}
    
    def _combine_mac_addresses(self, device: Dict) -> str:
        """Combine all MAC addresses into a single field"""
        macs = []
        if device.get('wiFiMacAddress'):
            macs.append(device['wiFiMacAddress'])
        if device.get('ethernetMacAddress'):
            macs.append(device['ethernetMacAddress'])
         
        # Remove duplicates while preserving order
        unique_macs = []
        for mac in macs:
            if mac not in unique_macs:
                unique_macs.append(mac)
        
        return '\n'.join(unique_macs) if unique_macs else None

    def sync_to_snipeit(self) -> Dict:
        """Main sync function"""
        print("Starting Intune synchronization...")
        
        if not self.authenticate():
            return {'error': 'Authentication failed'}
        
        self.asset_matcher.clear_all_caches()
        
        # Fetch devices from Intune
        intune_devices = self.get_managed_devices()
        print(f"Found {len(intune_devices)} devices in Intune")
        
        # DEBUG: Clear existing logs once if debug
        if debug_logger.debug:
            debug_logger._clear_all_debug_logs()
        
        # --- DEBUG: Print raw devices ---
        if intune_devices and debug_logger.debug:
            for device in intune_devices:
                raw_message = "\n--- RAW INTUNE DEVICE ---\n" + \
                    json.dumps(device, indent=2) + \
                        "\n----------------------------------------\n"
                debug_logger._raw_data_log(raw_message)     
            
        # Transform and prepare for Snipe-IT
        transformed_devices = []
        for device in intune_devices:
            transformed = self.transform_intune_to_snipeit(device)
            transformed_devices.append(transformed)
        
        # --- DEBUG: Print transformed devices ---
        if transformed_devices and debug_logger.debug:
            for transformed_device in transformed_devices:
                transformed_message = "\n--- TRANSFORMED DEVICE ---\n" + \
                    json.dumps(transformed_device, indent=2) + \
                        "\n----------------------------------------\n"
                debug_logger._transformed_data_log(transformed_message)
        
        # Send to asset matcher for processing
        results = self.asset_matcher.process_scan_data('intune', transformed_devices)
        
        print(f"Sync complete: {results['created']} created, {results['updated']} updated, {results['failed']} failed")
        return results

if __name__ == "__main__":   
    sync = IntuneSync()
    sync.sync_to_snipeit()