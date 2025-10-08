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
        
        # Master flag for convenience
        self.is_enabled = self.intune_debug or self.nmap_debug
        
        # Create log directory
        self.log_dir = os.path.join("logs", "debug_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Purpose-based log files (all sources mixed, organized by stage)
        self.raw_data_log_file = os.path.join(self.log_dir, "raw_unparsed_data.log")
        self.parsed_data_log_file = os.path.join(self.log_dir, "parsed_asset_data.log")
        self.categorization_log_file = os.path.join(self.log_dir, "categorization_details.log")
        self.sync_summary_log_file = os.path.join(self.log_dir, "sync_summary.log")
    
    def clear_logs(self):
        """Clears all debug log files if any debugging is enabled."""
        if not self.is_enabled:
            return
        for log_file in [
            self.raw_data_log_file, 
            self.parsed_data_log_file, 
            self.categorization_log_file, 
            self.sync_summary_log_file
        ]:
            with open(log_file, "w", encoding="utf-8") as f:
                f.write("")
        
    def log_raw_host_data(self, source: str, host_identifier: str, data: dict):
        """
        Logs the unparsed, raw data object for a single host/device.
        
        Args:
            source: 'intune' or 'nmap'
            host_identifier: Device ID, IP, or hostname
            data: Raw data dictionary
        """
        # Check source-specific flag
        if not self._should_log(source):
            return
            
        message = (
            f"\n--- RAW UNPARSED DATA | {source.upper()} | Host: {host_identifier} ---\n" +
            json.dumps(data, indent=2, default=str) + 
            "\n" + "-"*50
        )
        self._write_log(message, self.raw_data_log_file)

    def log_parsed_asset_data(self, source: str, data: list):
            """
            Logs the final, parsed list of assets ready for syncing.
            
            Args:
                source: 'intune' or 'nmap'
                data: List of parsed asset dictionaries
            """
            if not self._should_log(source):
                return
                
            message = (
                f"\n--- PARSED ASSET DATA FROM {source.upper()} ---\n" +
                f"Found {len(data)} assets.\n" +
                json.dumps(data, indent=2, default=str) + 
                "\n" + "-"*50
            )
            self._write_log(message, self.parsed_data_log_file)
        
    def log_categorization(self, source: str, log_entry: str):
        """
        Logs the details during the asset categorization step.
        
        Args:
            source: 'intune' or 'nmap'
            log_entry: Pre-formatted log message
        """
        if not self._should_log(source):
            return
        self._write_log(log_entry, self.categorization_log_file)
        
    def log_sync_summary(self, source: str, results: dict):
        """
        Logs the final summary of the sync operation.
        
        Args:
            source: 'intune' or 'nmap'
            results: Results dictionary with 'created', 'updated', 'failed'
        """
        if not self._should_log(source):
            return
            
        message = (
            f"\n--- SYNC SUMMARY FOR {source.upper()} ---\n" +
            f"Created: {results.get('created', 0)}\n" +
            f"Updated: {results.get('updated', 0)}\n" +
            f"Failed:  {results.get('failed', 0)}\n" +
            "-"*50
        )
        self._write_log(message, self.sync_summary_log_file)

    def _should_log(self, source: str) -> bool:
        """Check if logging is enabled for the given source."""
        if source.lower() == 'intune':
            return self.intune_debug
        elif source.lower() == 'nmap':
            return self.nmap_debug
        else:
            # Unknown source, log if any debug is enabled
            return self.is_enabled

    def _write_log(self, message: str, log_file: str):
        """Internal method to write timestamped log entries."""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] {message}"
        try:
            with open(log_file, "a", encoding="utf-8") as f:
                f.write(log_entry + "\n")
        except IOError as e:
            print(f"Warning: Could not write to log file {log_file}: {e}")

debug_logger = AssetDebugLogger()