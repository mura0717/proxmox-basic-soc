
"""
Debug script to test the merging logic of Intune and Teams data.
It uses hardcoded raw asset data, transforms it, and runs the merge function
to display the final combined asset.
"""
import sys
import os
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from assets_sync_library.microsoft365_sync import Microsoft365Sync
from scanners.intune_scanner import IntuneScanner
from scanners.teams_scanner import TeamsScanner

def main():
    """
    Runs the debug merge process for a single hardcoded Intune and Teams asset.
    """
    print("--- Starting Microsoft 365 Merge Debug Test ---")

    intune_asset_raw = {
        "id": "0d05700f-f68d-4c52-8c00-7910cd549899",
        "userId": "db6056b7-a322-45ef-b86d-c20ff9d10611",
        "deviceName": "HB-Lokale_AndroidAOSP_7/2/2025_12:01 PM",
        "managedDeviceOwnerType": "company",
        "managementState": "managed",
        "enrolledDateTime": "2025-07-02T12:01:04Z",
        "lastSyncDateTime": "2025-10-29T08:28:12Z",
        "operatingSystem": "Android",
        "complianceState": "compliant",
        "jailBroken": "Unknown",
        "managementAgent": "intuneAosp",
        "osVersion": "13",
        "easActivated": False,
        "easDeviceId": "",
        "easActivationDateTime": "0001-01-01T00:00:00Z",
        "azureADRegistered": True,
        "deviceEnrollmentType": "androidAOSPUserOwnedDeviceEnrollment",
        "activationLockBypassCode": None,
        "emailAddress": "HB-Lokale@diabetes.dk",
        "azureADDeviceId": "e592ec56-5d25-4ee1-a35f-4a6f695e4886",
        "deviceRegistrationState": "registered",
        "deviceCategoryDisplayName": "Unknown",
        "isSupervised": False,
        "exchangeLastSuccessfulSyncDateTime": "0001-01-01T00:00:00Z",
        "exchangeAccessState": "none",
        "exchangeAccessStateReason": "none",
        "remoteAssistanceSessionUrl": None,
        "remoteAssistanceSessionErrorDetails": None,
        "isEncrypted": True,
        "userPrincipalName": "HB-Lokale@diabetes.dk",
        "model": "MeetingBar A30",
        "manufacturer": "Yealink",
        "imei": "",
        "complianceGracePeriodExpirationDateTime": "9999-12-31T23:59:59Z",
        "serialNumber": "803032F100002448",
        "phoneNumber": "",
        "androidSecurityPatchLevel": "2025-05-05",
        "userDisplayName": "HB-Lokale",
        "configurationManagerClientEnabledFeatures": None,
        "wiFiMacAddress": "",
        "deviceHealthAttestationState": None,
        "subscriberCarrier": "",
        "meid": "",
        "totalStorageSpaceInBytes": 50340036608,
        "freeStorageSpaceInBytes": 0,
        "managedDeviceName": "HB-Lokale_AndroidAOSP_7/2/2025_12:01 PM",
        "partnerReportedThreatState": "unknown",
        "requireUserEnrollmentApproval": None,
        "managementCertificateExpirationDate": "2026-05-03T10:32:33Z",
        "iccid": None,
        "udid": None,
        "notes": None,
        "ethernetMacAddress": None,
        "physicalMemoryInBytes": 0,
        "enrollmentProfileName": None,
        "deviceActionResults": []
    }

    teams_asset_raw = {
        "id": "a14c9a1a-3046-4d5f-8521-15f20c29d251",
        "deviceType": "collaborationBar",
        "notes": None,
        "companyAssetTag": None,
        "healthStatus": "healthy",
        "activityState": "unknown",
        "createdDateTime": "2024-01-23T12:22:07Z",
        "lastModifiedDateTime": "2025-11-10T08:48:04Z",
        "createdBy": None,
        "lastModifiedBy": None,
        "hardwareDetail": {
            "serialNumber": "803032f100002448",
            "uniqueId": "803032f100002448",
            "macAddresses": [
            "ETHERNET:249AD8D4558C"
            ],
            "manufacturer": "yealink",
            "model": "meetingbara30"
        },
        "currentUser": {
            "id": "db6056b7-a322-45ef-b86d-c20ff9d10611",
            "displayName": "HB-Lokale",
            "userIdentityType": "aadUser"
        }
    }

    # 1. Instantiate scanners and the main sync class
    intune_scanner = IntuneScanner()
    teams_scanner = TeamsScanner()
    ms365_sync = Microsoft365Sync()

    # 2. Transform the raw data into the standardized Snipe-IT format
    transformed_intune = intune_scanner.transform_intune_to_snipeit(intune_asset_raw)
    transformed_teams = teams_scanner.transform_teams_to_snipeit(teams_asset_raw)

    # 3. Merge the transformed data
    merged_asset = ms365_sync.merge_data(intune_data=[transformed_intune], teams_data=[transformed_teams])

    # 4. Print the final merged result
    print("\n--- Final Merged Asset ---")
    print(json.dumps(merged_asset, indent=2))
    print("--- End of Test ---")

if __name__ == "__main__":
    main()
