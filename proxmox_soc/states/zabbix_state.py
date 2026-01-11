"""
Zabbix State Manager
Handles host existence checks against Zabbix API.
"""

from typing import Dict, Optional

from proxmox_soc.states.base_state import BaseStateManager, StateResult
from proxmox_soc.config.hydra_settings import ZABBIX

# Assume you have or will create a Zabbix API client
# from proxmox_soc.zabbix.zabbix_api import ZabbixAPI


class ZabbixStateManager(BaseStateManager):
    """
    Manages host state against Zabbix.
    
    Uses Zabbix API to check for existing hosts by:
    - Hostname
    - IP address
    - MAC address (custom inventory field)
    """
    
    IDENTITY_PRIORITY = ('mac_addresses', 'last_seen_ip', 'name')
    
    def __init__(self):
        # self.api = ZabbixAPI(ZABBIX.url, ZABBIX.token)
        self._cache: Dict[str, Dict] = {}
    
    def generate_id(self, asset_data: Dict) -> Optional[str]:
        """Generate Zabbix-specific ID."""
        mac = asset_data.get('mac_addresses')
        if mac:
            return f"zabbix:mac:{mac}"
        
        ip = asset_data.get('last_seen_ip')
        if ip:
            return f"zabbix:ip:{ip}"
        
        name = asset_data.get('name')
        if name and not name.lower().startswith('device-'):
            return f"zabbix:name:{name}"
        
        return None
    
    def check(self, asset_data: Dict) -> StateResult:
        """Check if host exists in Zabbix."""
        asset_id = self.generate_id(asset_data)
        
        if not asset_id:
            return StateResult(
                action='skip',
                asset_id='',
                existing=None,
                reason='No suitable identifier for Zabbix'
            )
        
        existing = self._find_existing(asset_data)
        
        if existing:
            return StateResult(
                action='update',
                asset_id=asset_id,
                existing=existing,
                reason=f"Found Zabbix host ID: {existing.get('hostid')}"
            )
        
        if self._is_monitorable(asset_data):
            return StateResult(
                action='create',
                asset_id=asset_id,
                existing=None,
                reason='New monitorable host'
            )
        
        return StateResult(
            action='skip',
            asset_id=asset_id,
            existing=None,
            reason='Host not suitable for Zabbix monitoring'
        )
    
    def record(self, asset_id: str, asset_data: Dict, action: str) -> None:
        """Cache result (Zabbix API handles persistence)."""
        self._cache[asset_id] = {'action': action}
    
    def _find_existing(self, asset_data: Dict) -> Optional[Dict]:
        """Query Zabbix for existing host."""
        # Implement Zabbix API calls here
        # Example:
        # hosts = self.api.host.get(filter={'ip': asset_data.get('last_seen_ip')})
        # return hosts[0] if hosts else None
        return None  # Placeholder
    
    def _is_monitorable(self, asset_data: Dict) -> bool:
        """Determine if asset should be monitored in Zabbix."""
        # Must have an IP address
        if not asset_data.get('last_seen_ip'):
            return False
        
        # Skip certain device types
        device_type = asset_data.get('device_type', '').lower()
        if device_type in ('mobile', 'phone', 'tablet'):
            return False
        
        return True