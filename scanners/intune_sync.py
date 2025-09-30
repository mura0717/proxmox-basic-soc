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

class IntuneSync:
    """Microsoft Intune synchronization service"""
    
    def __init__(self):
        # Load credentials from environment
        self.tenant_id = os.getenv('AZURE_TENANT_ID')
        self.client_id = os.getenv('AZURE_CLIENT_ID')
        self.client_secret = os.getenv('AZURE_CLIENT_SECRET')
        
        # Debugging setup
        self.debug = os.getenv('INTUNE_DEBUG', '0') == '1'
        self.log_dir = os.path.join("logs", "debug_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        self.device_log_file = os.path.join(self.log_dir, "device_data_log.txt")
        self.raw_log_file = os.path.join(self.log_dir, "raw_intune_log.txt")
        self.transformed_log_file = os.path.join(self.log_dir, "transformed_log.txt")
        self._device_log_count = 0
        self._raw_log_count = 0
        self._transformed_log_count = 0
        
        if not all([self.tenant_id, self.client_id, self.client_secret]):
            raise ValueError("Azure credentials not configured in environment")
        
        self.asset_matcher = AssetMatcher()
        self.graph_url = "https://graph.microsoft.com/v1.0"
        self.access_token = None
    
    # Debugging functions
    def _clear_log_file(self, log_file: str):
        """Overwrite a log file."""
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("") 
            
    def _clear_all_debug_logs(self):
        """Clear all debug log files at the start of each sync."""
        self._clear_log_file(self.device_log_file)
        self._clear_log_file(self.raw_log_file)
        self._clear_log_file(self.transformed_log_file)
        self._device_log_count = 0
        self._raw_log_count = 0
        self._transformed_log_count = 0 
                
    def _debug_log(self, message: str, log_file: str, print_terminal: bool = True):
        """Centralized debug logging to file and optionally to terminal."""
        if self.debug:
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(message + "\n")
            except IOError as e:
                print(f"Warning: Could not write to log file {log_file}: {e}")
            if print_terminal:
                print(message)
        else:
            return
                
    def _device_data_log(self, message: str, print_terminal: bool = True):
        print_terminal = self._device_log_count < 3
        self._device_log_count += 1
        self._debug_log(message, self.device_log_file, print_terminal=print_terminal)

    def _raw_data_log(self, message: str, print_terminal: bool = True):
        print_terminal = self._device_log_count < 3
        self._raw_log_count += 1
        self._debug_log(message, self.raw_log_file, print_terminal=print_terminal)

    def _transformed_data_log(self, message: str, print_terminal: bool = True):
        print_terminal = self._device_log_count < 3
        self._transformed_log_count += 1
        self._debug_log(message, self.transformed_log_file, print_terminal=print_terminal)
    
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
            'device_type': self._determine_device_type(intune_device),
            'device_health_attestation_state': intune_device.get('deviceHealthAttestationState'),
            'partner_reported_threat_state': intune_device.get('partnerReportedThreatState'),
            'notes': intune_device.get('notes'),
            
            # Software Inventory
            'configuration_manager_client_enabled_features': intune_device.get('configurationManagerClientEnabledFeatures'),
            
            # Cloud Resource Information
            'cloud_provider': self._determine_cloud_provider(intune_device),        
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
    
    def _determine_cloud_provider(self, intune_device: Dict) -> str | None: 
        """ Determines the cloud provider based on device manufacturer and model. """ 
        manufacturer = intune_device.get('manufacturer', '').lower() 
        model = intune_device.get('model', '').lower() 
        
        if 'microsoft corporation' in manufacturer and 'virtual machine' in model: 
            return 'Azure'
        elif 'amazon' or "aws" in manufacturer or 'amazon ec2' in model: 
            return 'AWS'
        else:
            return 'On-Premise'
    
    def _determine_device_type(self, device: Dict) -> str:
        laptop_markers = {'laptop', 'notebook', 'book', 'zenbook', 'vivobook', 'thinkpad', 'latitude', 
                      'xps', 'precision', 'elitebook', 'probook', 'spectre', 'envy', 'surface laptop', 
                      'travelmate', 'gram', 'ideapad', 'chromebook'}
        
        lenovo_laptop_prefixes = {'20', '21', '11', '40'}
        
        """Determine device type from Intune data"""
        os_type = device.get('operatingSystem', '').lower()
        device_type = device.get('deviceType', '').lower()
        model = device.get('model', '').lower()
        manufacturer = device.get('manufacturer', '').lower()
        
        """Device data log for debugging"""
        if self.debug:
            device_name = device.get('deviceName', 'Unknown Device')
            os_type = device.get('operatingSystem', '').lower()
            model = device.get('model', '').lower()
            manufacturer = device.get('manufacturer', '').lower()
            cloud_provider = self._determine_cloud_provider(device)
            log_entry = (
                f"--- Device: {device_name} ---\n"
                f"  OS Type:      {os_type}\n"
                f"  Model:        {model}\n"
                f"  Manufacturer: {manufacturer}\n"
                f"  Cloud Provider: {cloud_provider}\n"
                f"{'-'*50}\n"
            )
            self._device_data_log(log_entry)
        
        """Categorizing logic based on device data"""
        if ('vmware' in manufacturer or 'virtualbox' in manufacturer or 'qemu' in manufacturer or 'microsoft corporation' in manufacturer) and ('virtual machine' in model or 'vm' in model):
            return 'Virtual Machine'        
        if 'server' in os_type or 'server' in model:
            return 'Server'
        elif 'ios' in os_type or 'iphone' in model:
            return 'Mobile Phone'
        elif 'ipad' in os_type or 'ipad' in model:
            return 'Tablet'
        elif 'android' in os_type or device_type == 'android':
            if 'tablet' in model or 'tab' in model or manufacturer in ['samsung', 'lenovo', 'huawei']:
                return 'Tablet'
            elif 'meetingbar' in model or 'roompanel' in model or 'ctp' in model:
                return 'IoT Devices' 
            return 'Mobile Phone'
        elif 'windows' in os_type or device_type in ['windows', 'windowsrt', 'desktop']:
            if any(keyword in model for keyword in laptop_markers):
                return 'Laptop'
            elif manufacturer == 'lenovo' and any(model.startswith(prefix) for prefix in lenovo_laptop_prefixes):
                return 'Laptop'  # Handles codes like '20t0001jmx', '21ls001umx'
            elif 'desktop' in model or device_type == 'desktop':
                return 'Desktop'
            return 'Laptop'
        elif 'mac' in os_type:
            if 'macbook' in model:
                return 'Laptop'
            elif any(keyword in model for keyword in ['imac', 'mac mini', 'mac pro']):
                return 'Desktop'
            return 'Laptop'
        elif 'iot' in device_type:
            return 'IoT Devices'
        else:
            return 'Other Device'

    def sync_to_snipeit(self) -> Dict:
        """Main sync function"""
        if self.debug:
            self._clear_all_debug_logs()   
        print("Starting Intune synchronization...")
        
        if not self.authenticate():
            return {'error': 'Authentication failed'}
        
        # Fetch devices from Intune
        intune_devices = self.get_managed_devices()
        print(f"Found {len(intune_devices)} devices in Intune")
        
        # --- DEBUG: Print the first raw device from Intune ---
        if intune_devices and self.debug:
            for device in intune_devices:
                raw_message = "\n--- RAW INTUNE DEVICE ---\n" + \
                    json.dumps(device, indent=2) + \
                        "\n----------------------------------------\n"
                self._raw_data_log(raw_message)     
            
        # Transform and prepare for Snipe-IT
        transformed_devices = []
        for device in intune_devices:
            transformed = self.transform_intune_to_snipeit(device)
            transformed_devices.append(transformed)
        
        # --- DEBUG: Print the first transformed device ---
        if transformed_devices and self.debug:
            for transformed_device in transformed_devices:
                transformed_message = "\n--- TRANSFORMED DEVICE ---\n" + \
                    json.dumps(transformed_device, indent=2) + \
                        "\n----------------------------------------\n"
                self._transformed_data_log(transformed_message)
        
        # Send to asset matcher for processing
        results = self.asset_matcher.process_scan_data('intune', transformed_devices)
        
        print(f"Sync complete: {results['created']} created, {results['updated']} updated, {results['failed']} failed")
        return results

if __name__ == "__main__":   
    sync = IntuneSync()
    sync.sync_to_snipeit()