import os
import sys
import json
from datetime import datetime 

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AssetDebugLogger:
    """Determines asset type and category based on attributes."""

    def __init__(self):
        self.intune_debug = os.getenv('INTUNE_DEBUG', '0') == '1'
        self.nmap_debug = os.getenv('NMAP_DEBUG', '0') == '1'
        
        # Create log directory
        self.log_dir = os.path.join("logs", "debug_logs")
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Shared logs (categorization data from both sources)
        self.asset_log_file = os.path.join(self.log_dir, "asset_data_log.txt")
        
        # Intune-specific logs
        self.raw_intune_log_file = os.path.join(self.log_dir, "raw_intune_log.txt")
        self.transformed_intune_log_file = os.path.join(self.log_dir, "transformed_log.txt")
        self.asset_all_details_log_file = os.path.join(self.log_dir, "all_intune_asset_details_log.txt")
        
        # Nmap-specific logs
        self.raw_nmap_log_file = os.path.join(self.log_dir, "raw_nmap_log.txt")
        
        # Counters
        self._asset_log_count = 0
        self._intune_raw_count = 0
        self._intune_transformed_count = 0
        self._nmap_raw_count = 0
        self._nmap_transformed_count = 0
        self._asset_all_details_log_count = 0
    
    def _clear_log_file(self, log_file: str):
        """Overwrite a log file."""
        with open(log_file, "w", encoding="utf-8") as f:
            f.write("")

    def _clear_all_debug_logs(self):
        """Clear all debug log files at the start of each sync."""
        log_files= [
            self.asset_log_file, 
            self.asset_all_details_log_file, 
            self.raw_intune_log_file, 
            self.transformed_intune_log_file, self.raw_nmap_log_file
        ]
        
        for log_file in log_files:
            self._clear_log_file(log_file)
        
        # Reset counters
        self._asset_log_count = 0
        self._intune_raw_count = 0
        self._intune_transformed_count = 0
        self._nmap_raw_count = 0
        self._nmap_transformed_count = 0
        self._asset_all_details_log_count = 0
        
    def _debug_log(self, message: str, log_file: str, print_terminal: bool = True):
        """Centralized debug logging to file and optionally to terminal."""
        timestamp = datetime.now().isoformat()
        message = f"[{timestamp}] {message}"
        if self.intune_debug or self.nmap_debug:
            try:
                with open(log_file, "a", encoding="utf-8") as f:
                    f.write(message + "\n")
            except IOError as e:
                print(f"Warning: Could not write to log file {log_file}: {e}")
            if print_terminal:
                print(message)
        else:
            return

    def _asset_data_log(self, message: str, print_terminal: bool = False):
        #print_terminal = self._asset_log_count < 3
        self._asset_log_count += 1
        self._debug_log(message, self.asset_log_file, print_terminal=print_terminal)

    def _intune_raw_data_log(self, message: str, print_terminal: bool = False):
        #print_terminal = self._raw_log_count < 3
        self._raw_log_count += 1
        self._debug_log(message, self.raw_intune_log_file, print_terminal=print_terminal)

    def _intune_transformed_data_log(self, message: str, print_terminal: bool = False):
        #print_terminal = self._transformed_log_count < 3
        self._transformed_log_count += 1
        self._debug_log(message, self.transformed_intune_log_file, print_terminal=print_terminal)
    
    def _log_asset_full_details (self, details: dict, label: str, print_terminal: bool = True):
        formatted_message = f"\n--- {label} ---\n" + \
                            json.dumps(details, indent=2) + \
                            "\n----------------------------------------\n"
        print_terminal = self._asset_all_details_log_count < 3
        self._asset_all_details_log_count += 1
        self._debug_log(formatted_message, self.asset_all_details_log_file, print_terminal=print_terminal)
        
    def _nmap_raw_data_log(self, message: str, print_terminal: bool = False):
        """Log raw Nmap scan results"""
        self._nmap_raw_count += 1
        self._debug_log(message, self.raw_nmap_log_file, self.nmap_debug, print_terminal)
    
    def _nmap_transformed_data_log(self, message: str, print_terminal: bool = False):
        """Log transformed Nmap data ready for Snipe-IT"""
        self._nmap_transformed_count += 1
        self._debug_log(message, self.transformed_nmap_log_file, self.nmap_debug, print_terminal)
        
debug_logger = AssetDebugLogger()