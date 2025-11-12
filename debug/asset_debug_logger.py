import os
import sys
import json
from datetime import datetime 

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AssetDebugLogger:
    """Determines asset type and category based on attributes."""

    def __init__(self):
        # Granular debug flags (can be set independently)
        self.intune_debug = os.getenv('INTUNE_DEBUG', '0') == '1'
        self.nmap_debug = os.getenv('NMAP_DEBUG', '0') == '1'
        self.teams_debug = os.getenv('TEAMS_DEBUG', '0') == '1'
        self.snmp_debug = os.getenv('SNMP_DEBUG', '0') == '1' # Not yet implemented
        self.microsoft365_debug = os.getenv('MICROSOFT365_DEBUG', '0') == '1'
        
        # Master flag for convenience
        self.is_enabled = self.intune_debug or self.nmap_debug or self.teams_debug or self.microsoft365_debug
        
        print(f"[DEBUG_LOGGER]: Initializing. INTUNE_DEBUG={os.getenv('INTUNE_DEBUG', '0')} (internal: {self.intune_debug}), "
              f"NMAP_DEBUG={os.getenv('NMAP_DEBUG', '0')} (internal: {self.nmap_debug}). Overall enabled: {self.is_enabled}, "
              f"TEAMS_DEBUG={os.getenv('TEAMS_DEBUG', '0')} (internal: {self.teams_debug}). "
              f"MICROSOFT365_DEBUG={os.getenv('MICROSOFT365_DEBUG', '0')} (internal: {self.microsoft365_debug})."
              )

        # Create log directory
        self.log_dir = os.path.join("logs", "debug_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Purpose-based log files
        self.log_files = {
            'intune': {
                'raw': os.path.join(self.log_dir, 'intune_raw_unparsed_data.log'),
                'parsed': os.path.join(self.log_dir, 'intune_parsed_asset_data.log'),
                'categorization': os.path.join(self.log_dir, 'intune_categorization_details.log'),
                'summary': os.path.join(self.log_dir, 'intune_sync_summary.log'),
                'final_payload': os.path.join(self.log_dir, 'intune_final_payload.log'),
            },
            'nmap': {
                'raw': os.path.join(self.log_dir, 'nmap_raw_unparsed_data.log'),
                'parsed': os.path.join(self.log_dir, 'nmap_parsed_asset_data.log'),
                'categorization': os.path.join(self.log_dir, 'nmap_categorization_details.log'),
                'summary': os.path.join(self.log_dir, 'nmap_sync_summary.log'),
                'final_payload': os.path.join(self.log_dir, 'nmap_final_payload.log'),
            },
            'teams': {
                'raw': os.path.join(self.log_dir, 'teams_raw_unparsed_data.log'),
                'parsed': os.path.join(self.log_dir, 'teams_parsed_asset_data.log'),
                'categorization': os.path.join(self.log_dir, 'teams_categorization_details.log'),
                'summary': os.path.join(self.log_dir, 'teams_sync_summary.log'),
                'final_payload': os.path.join(self.log_dir, 'teams_final_payload.log'),
            },
            'microsoft365': {
                'raw': os.path.join(self.log_dir, 'microsoft365_raw_merged_data.log'),
                'parsed': os.path.join(self.log_dir, 'microsoft365_parsed_asset_data.log'),
                'categorization': os.path.join(self.log_dir, 'microsoft365_categorization_details.log'),
                'summary': os.path.join(self.log_dir, 'microsoft365_sync_summary.log'),
                'final_payload': os.path.join(self.log_dir, 'microsoft365_final_payload.log'),
            }
        }
    
    def _get_log_path(self, source: str, purpose: str) -> str | None:
        """Helper to get the correct log file path for a source and purpose."""  
        log_path = self.log_files.get(source.lower(), {}).get(purpose)
        return self.log_files.get(source.lower(), {}).get(purpose)
    
    
    def _should_log(self, source: str) -> bool:
        """Check if logging is enabled for the given source."""
        source_lower = source.lower()
        if source_lower == 'intune': result = self.intune_debug
        elif source_lower == 'nmap': result = self.nmap_debug
        elif source_lower == 'teams': result = self.teams_debug
        elif source_lower == 'snmp': result = self.snmp_debug
        elif source_lower == 'microsoft365': result = self.microsoft365_debug
        else: result = False
        
        print(f" [DEBUG_LOGGER] asset_debug_logger: _should_log called for source '{source_lower}'. Result: {result}")
        return result
    
    def clear_logs(self, source: str):
        """Clears all log files for a specific source."""
        if not self._should_log(source): return
        
        source_files = self.log_files.get(source.lower(), {})
        for file_path in source_files.values():
            with open(file_path, "w", encoding="utf-8") as f: f.write("")
        
    def log_raw_host_data(self, source: str, host_identifier: str, data: dict):
        if not self._should_log(source): return
        log_path = self._get_log_path(source, 'raw')
        if not log_path: return
        
        message = f"\n--- RAW DATA | Host: {host_identifier} ---\n" + \
                  json.dumps(data, indent=2, default=str) + "\n" + "-"*50
        self._write_log(message, log_path)

    def log_parsed_asset_data(self, source: str, data: list):
        if not self._should_log(source): return
        log_path = self._get_log_path(source, 'parsed')
        if not log_path: return
        
        message = f"\n--- PARSED ASSET DATA ---\n" + \
                  f"Found {len(data)} assets.\n" + \
                  json.dumps(data, indent=2) + "\n" + "-"*50
        self._write_log(message, log_path)
        
    def log_categorization(self, source: str, log_entry: str):
        if not self._should_log(source): return
        log_path = self._get_log_path(source, 'categorization')
        if not log_path: return
        self._write_log(log_entry, log_path)
        
    def log_sync_summary(self, source: str, results: dict):
        if not self._should_log(source): return
        log_path = self._get_log_path(source, 'summary')
        if not log_path: return
        
        message = f"\n--- SYNC SUMMARY ---\n" + \
                  f"Created: {results.get('created', 0)}\n" + \
                  f"Updated: {results.get('updated', 0)}\n" + \
                  f"Failed:  {results.get('failed', 0)}\n" + "-"*50
        self._write_log(message, log_path)

    def log_final_payload(self, source: str, action: str, asset_name: str, payload: dict):
        """Logs the final payload being sent to the Snipe-IT API."""
        if not self._should_log(source): return
        log_path = self._get_log_path(source, 'final_payload')
        if not log_path: return

        message = f"\n--- FINAL PAYLOAD | Action: {action.upper()} | Asset: {asset_name} ---\n" + \
                  json.dumps(payload, indent=2, default=str) + "\n" + "-"*50
        self._write_log(message, log_path)
        print(f"Final Log Message: {message}")

    def _write_log(self, message: str, log_file: str):
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        absolute_log_file = os.path.abspath(log_file)
        try:
            with open(log_file, "a", encoding="utf-8") as f: f.write(log_entry + "\n")
            print(f"DEBUG_LOGGER: Successfully wrote to '{absolute_log_file}'.")
        except IOError as e:
            print(f"Warning: Could not write to log file {log_file}: {e}")

debug_logger = AssetDebugLogger()