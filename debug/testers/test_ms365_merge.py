"""
Debug script to test the merging logic of Intune and Teams data.
It uses hardcoded raw asset data, transforms it, and runs the merge function
to display the final combined asset.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asset_sync_library.ms365_sync import Microsoft365Sync
from scanners.intune_scanner import IntuneScanner
from scanners.teams_scanner import TeamsScanner

def ms365_merge_tester():

    print("--- Starting Microsoft 365 Merge Debug Test ---")

    intune_asset_raw_sample = {
        "id": "734482e2-bec7-47ba-bd51-4897355f2766",
        "userId": "f74d0f00-ac95-4725-8241-d8f0527cc06a",
        "deviceName": "kantine_AndroidAOSP_5/1/2025_2:56 PM",
        "managedDeviceOwnerType": "company",
        "managementState": "managed",
        "enrolledDateTime": "2025-05-01T14:56:21Z",
        "lastSyncDateTime": "2025-11-13T04:19:59Z",
        "operatingSystem": "Android",
        "complianceState": "compliant",
        "jailBroken": "Unknown",
        "managementAgent": "intuneAosp",
        "osVersion": "10",
        "easActivated": False,
        "easDeviceId": "",
        "easActivationDateTime": "0001-01-01T00:00:00Z",
        "azureADRegistered": True,
        "deviceEnrollmentType": "androidAOSPUserOwnedDeviceEnrollment",
        "activationLockBypassCode": None,
        "emailAddress": "kantine@diabetes.dk",
        "azureADDeviceId": "cc486eb9-8c93-462a-bb0f-adcef7d50e88",
        "deviceRegistrationState": "registered",
        "deviceCategoryDisplayName": "Unknown",
        "isSupervised": False,
        "exchangeLastSuccessfulSyncDateTime": "0001-01-01T00:00:00Z",
        "exchangeAccessState": "none",
        "exchangeAccessStateReason": "none",
        "remoteAssistanceSessionUrl": None,
        "remoteAssistanceSessionErrorDetails": None,
        "isEncrypted": True,
        "userPrincipalName": "kantine@diabetes.dk",
        "model": "RoomPanel",
        "manufacturer": "Yealink",
        "imei": "",
        "complianceGracePeriodExpirationDateTime": "9999-12-31T23:59:59Z",
        "serialNumber": "803110D072402058",
        "phoneNumber": "",
        "androidSecurityPatchLevel": "2023-06-05",
        "userDisplayName": "Kantine",
        "configurationManagerClientEnabledFeatures": None,
        "wiFiMacAddress": "",
        "deviceHealthAttestationState": None,
        "subscriberCarrier": "",
        "meid": "",
        "totalStorageSpaceInBytes": 8709472256,
        "freeStorageSpaceInBytes": 0,
        "managedDeviceName": "kantine_AndroidAOSP_5/1/2025_2:56 PM",
        "partnerReportedThreatState": "unknown",
        "requireUserEnrollmentApproval": None,
        "managementCertificateExpirationDate": "2026-05-01T00:59:41Z",
        "iccid": None,
        "udid": None,
        "notes": None,
        "ethernetMacAddress": None,
        "physicalMemoryInBytes": 0,
        "enrollmentProfileName": None,
        "deviceActionResults": []
        }

    teams_asset_raw_sample = {
        "id": "d86782f6-796a-4f8c-985e-dde0b660ab04",
        "deviceType": "teamsRoom",
        "notes": None,
        "companyAssetTag": None,
        "healthStatus": "healthy",
        "activityState": "idle",
        "createdDateTime": "2022-05-10T11:25:16Z",
        "lastModifiedDateTime": "2025-11-13T08:27:24Z",
        "createdBy": None,
        "lastModifiedBy": None,
        "hardwareDetail": {
            "serialNumber": "806046D110001508",
            "uniqueId": "11a209e72eddbaaf6b711b56ccca1b60279cb5f59c2a0f9bd9f90f4020043a6a",
            "macAddresses": [
            "UNKNOWN:A4:17:91:23:5C:74",
            "UNKNOWN:4C:77:CB:DC:23:1E"
            ],
            "manufacturer": "yealink",
            "model": "core2kit"
        },
        "currentUser": {
            "id": "f74d0f00-ac95-4725-8241-d8f0527cc06a",
            "displayName": "Kantine",
            "userIdentityType": "aadUser"
        }
        }   

    # 1. Instantiate scanners and the main sync class
    intune_scanner = IntuneScanner()
    teams_scanner = TeamsScanner()
    ms365_sync = Microsoft365Sync()

    # 2. Transform the raw data into the standardized Snipe-IT format
    transformed_raw_intune = intune_scanner.transform_intune_to_snipeit(intune_asset_raw_sample)
    print("\n--- Transformed Intune Asset ---")
    print(json.dumps(transformed_raw_intune, indent=2))
    print("--- End of Transformed Intune Asset ---")
    
    transformed_raw_teams = teams_scanner.transform_teams_to_snipeit(teams_asset_raw_sample)
    print("\n--- Transformed Teams Asset ---")
    print(json.dumps(transformed_raw_teams, indent=2))
    print("--- End of Transformed Teams Asset ---")

    # 3. Merge the transformed data
    merged_asset = ms365_sync.merge_data(intune_data=[transformed_raw_intune], teams_data=[transformed_raw_teams])

    # 4. Print the final merged result
    print("\n--- Final Merged Asset ---")
    print(json.dumps(merged_asset, indent=2))
    print("--- End of Test ---")

if __name__ == "__main__":
    ms365_merge_tester()
