"""
Utility for merging raw data coming from Microsoft Intune and Microsoft Teams into a unified asset list.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional

from proxmox_soc.config.ms365_service import Microsoft365Service
from proxmox_soc.scanners.intune_scanner import IntuneScanner
from proxmox_soc.scanners.teams_scanner import TeamsScanner
from proxmox_soc.utils.mac_utils import normalize_mac_semicolon
from proxmox_soc.debug.tools.asset_debug_logger import debug_logger 
from proxmox_soc.debug.categorize_from_logs.ms365_categorize_from_logs import ms365_debug_categorization
from proxmox_soc.config.mac_config import CTP18

class Microsoft365Aggregator:
    """Microsoft365 data merging service"""
    
    def __init__(self):
        self.microsoft365 = Microsoft365Service()
        self.intune_sync = IntuneScanner()
        self.teams_sync = TeamsScanner()
        
    def _prepare_asset_dictionaries(self, intune_data: List[Dict], teams_data: List[Dict]) -> tuple[Dict, Dict]:
        """Creates dictionaries of assets keyed by serial number for quick lookups."""
        print("Preparing asset dictionaries...")
        intune_assets_by_serial = {
            asset.get('serial'): asset 
            for asset in intune_data if asset.get('serial')
        }
        teams_assets_by_serial = {
            asset.get('serial'): asset 
            for asset in teams_data if asset.get('serial')
        }
        
        print(f"  Intune assets with serial: {len(intune_assets_by_serial)}")
        print(f"  Teams assets with serial: {len(teams_assets_by_serial)}")
        
        return intune_assets_by_serial, teams_assets_by_serial
    
    def _merge_asset_data(self, base: Dict, overlay: Dict) -> Dict:
        """
        Merge two asset dictionaries with overlay taking precedence for non-empty values.
        """
        merged = {**base}
        for key, value in overlay.items():
            # Only overlay if value is meaningful
            if value is not None and value != '' and value != []:
                merged[key] = value
        return merged

    def _merge_intune_with_teams(self, intune_assets_by_serial: Dict, teams_assets_by_serial: Dict) -> tuple[List[Dict], set]:
        """Merges Teams data into Intune assets, prioritizing Intune data."""
        print("Merging transformed Intune assets with corresponding Teams data...")
        merged_assets = []
        processed_serials = set()

        for serial, intune_asset in intune_assets_by_serial.items():
            intune_asset['_source'] = 'intune'  # Tag source for merge logic
            teams_asset = teams_assets_by_serial.get(serial)
    
            if teams_asset:
                if debug_logger.ms365_debug:
                    print(f"  ✓ Merging Teams data for: {serial}")
                teams_asset['_source'] = 'teams'
                merged_asset = self._merge_asset_data(teams_asset, intune_asset)
            else:
                if debug_logger.ms365_debug:
                    print(f"  ✓ Intune only: {serial}")
                merged_asset = intune_asset
            
            merged_assets.append(merged_asset)
            processed_serials.add(serial)
            
        return merged_assets, processed_serials

    def _add_unmatched_teams_assets(self, merged_assets: List[Dict], processed_serials: set, teams_data: List[Dict], intune_data: List[Dict]):
        """Handles Teams assets not matched by serial, with a fallback merge on user ID."""
        if debug_logger.ms365_debug:
            print("Processing unmatched Teams-only assets...")
        intune_assets_by_user_id = {
            asset['primary_user_id']: asset 
            for asset in intune_data if asset.get('primary_user_id')
        }
        merged_assets_by_serial = {asset['serial']: asset for asset in merged_assets if asset.get('serial')}
        for teams_asset in teams_data:
            serial = teams_asset.get('serial')
            if serial and serial in processed_serials:
                continue
            user_id = teams_asset.get('primary_user_id')
            intune_match = intune_assets_by_user_id.get(user_id)
            intune_serial = intune_match.get('serial') if intune_match else None

            if intune_match and intune_serial in merged_assets_by_serial:
                # Fallback merge logic for shared user accounts
                if not serial:
                    if debug_logger.ms365_debug:
                        print(f"  ✓ Fallback merge for user ID {user_id} (Intune S/N: {intune_serial}, Teams asset has no S/N)")
                    # Use robust merge to preserve Intune data priority while filling gaps from Teams
                    target_asset = merged_assets_by_serial[intune_serial]
                    merged_result = self._merge_asset_data(teams_asset, target_asset)
                    target_asset.clear()
                    target_asset.update(merged_result)
                else:
                    if debug_logger.ms365_debug:
                        print(f"  ✗ Not merging for user ID {user_id}. Assets have different serials ({intune_serial} vs {serial}). Treating as separate devices.")
                    teams_asset['last_update_source'] = 'microsoft365'
                    teams_asset['last_update_at'] = datetime.now(timezone.utc).isoformat()
                    merged_assets.append(teams_asset)
            else:
                # This is a truly unmatched Teams asset
                if debug_logger.ms365_debug:
                    print(f"  ✓ Teams only: {serial or teams_asset.get('name', 'Unknown')}")
                # Ensure source metadata is set for truly unmatched Teams assets
                teams_asset['last_update_source'] = 'microsoft365'
                teams_asset['last_update_at'] = datetime.now(timezone.utc).isoformat()
                merged_assets.append(teams_asset)
    
    def _add_unmatched_intune_assets(self, merged_assets: List[Dict], intune_data: List[Dict]):
        """Adds Intune assets that did not have a serial number."""
        if debug_logger.ms365_debug:
            print("Processing unmatched Intune assets (without serial numbers)...")
        for intune_asset in intune_data:
            if not intune_asset.get('serial'):
                merged_assets.append(intune_asset)

    def _enrich_assets_with_static_macs(self, merged_assets: List[Dict]):
        """Adds MAC addresses from a static MAC address list for missing assets."""
        print("Enriching assets with static MAC addresses from mac_config...")
        
        static_mac_map = {
            device['serial']: device['mac_address']
            for device in CTP18.values() if 'serial' in device and 'mac_address' in device
        }
        
        for asset in merged_assets:
            if not asset.get('mac_addresses'):
                serial = asset.get('serial')
                if serial and serial in static_mac_map:
                    asset['mac_addresses'] = normalize_mac_semicolon(static_mac_map[serial])
        
    def merge_data(self, intune_data: Optional[List[Dict]] = None, teams_data: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Merges Intune and Teams data. If data lists are not provided, fetches them from the scanners.
        """
        # Fetch data from scanners if not provided
        if intune_data is None or teams_data is None:
            raw_intune_data, intune_data = self.intune_sync.get_transformed_assets()
            raw_teams_data, teams_data = self.teams_sync.get_transformed_assets()
            
            if debug_logger.ms365_debug:
                combined_raw_data = {'intune_assets': raw_intune_data, 'teams_assets': raw_teams_data}
                debug_logger.log_raw_host_data('ms365', 'raw-unmerged-data', combined_raw_data)
        
        # Prepare dictionaries keyed by serial number for merging
        intune_assets_by_serial, teams_assets_by_serial = self._prepare_asset_dictionaries(intune_data, teams_data) # This can be simplified now
        
        # Perform the merge operations
        merged_assets, processed_serials = self._merge_intune_with_teams(intune_assets_by_serial, teams_assets_by_serial)
        self._add_unmatched_teams_assets(merged_assets, processed_serials, teams_data, intune_data)
        self._add_unmatched_intune_assets(merged_assets, intune_data)
        
        # Enrich the final list with static MACs for devices that are missing them
        self._enrich_assets_with_static_macs(merged_assets)

        return merged_assets
    
    def collect_assets(self) -> List[Dict]:
        """Entry point for orchestrator - Fetches and merges all Microsoft 365 assets."""
        print("Starting Microsoft 365 asset collection...")
        
        if debug_logger.ms365_debug:
            debug_logger.clear_logs('ms365')

        merged_assets = self.merge_data()
        print(f"Total of {len(merged_assets)} unique assets collected.")
        
        if debug_logger.ms365_debug:
            for asset in merged_assets:
                debug_logger.log_parsed_asset_data('ms365', asset)
        
        return merged_assets

    def sync_to_logs(self):
        """Fetches live data and generates the raw and parsed log files for debugging."""
        print("Starting Microsoft 365 debug logging...")

        # 1. Fetch live data once
        raw_intune_data, transformed_intune = self.intune_sync.get_transformed_assets()
        raw_teams_data, transformed_teams = self.teams_sync.get_transformed_assets()
        combined_raw_data = {'intune_assets': raw_intune_data, 'teams_assets': raw_teams_data}

        # 2. Clear old logs and write the new raw data log
        debug_logger.clear_logs('ms365')
        debug_logger.log_raw_host_data('ms365', 'raw-unmerged-data', combined_raw_data)
        print(f"\nRaw data log file has been created at: {debug_logger.log_files['ms365']['raw']}")

        # 3. Merge the already-fetched data and write the parsed data log
        merged_assets = self.merge_data(intune_data=transformed_intune, teams_data=transformed_teams)
        print(f"Found {len(merged_assets)} unique assets from Intune and Teams")
        for asset in merged_assets: # Log each asset individually to the parsed log
            debug_logger.log_parsed_asset_data('ms365', asset)
        print(f"\nMerged transformed data log file has been created at: {debug_logger.log_files['ms365']['parsed']}")

def main():
    """CLI entry point for standalone execution."""
    if ms365_debug_categorization.debug:
        print("Running Microsoft 365 categorization from existing logs...")
        ms365_debug_categorization.write_m365_assets_to_logfile()
        return

    aggregator = Microsoft365Aggregator()
    if debug_logger.ms365_debug:
        aggregator.sync_to_logs() 
    else:
        assets = aggregator.collect_assets()
        print(f"\n MS365 Asset Collection complete. Found {len(assets)} assets.")
         
if __name__ == "__main__":
    main()

  
    
