#!/usr/bin/env python3
"""
OpenVAS Vulnerability Scanner Integration
"""

import os
import time
from datetime import datetime, timezone
from typing import List, Dict, Optional
from gvm.connections import UnixSocketConnection
from gvm.protocols.gmp import Gmp
from gvm.transforms import EtreeTransform
from ..assets_sync_library.asset_matcher import AssetMatcher

class OpenVASScanner:
    """OpenVAS/GVM vulnerability scanner integration"""
    
    def __init__(self):
        self.socket_path = '/var/run/gvmd/gvmd.sock'
        self.username = os.getenv('OPENVAS_USER', 'admin')
        self.password = os.getenv('OPENVAS_PASSWORD')
        self.asset_matcher = AssetMatcher()
    
    def scan_target(self, target_ip: str) -> Optional[Dict]:
        """Run vulnerability scan on single target"""
        
        connection = UnixSocketConnection(path=self.socket_path)
        transform = EtreeTransform()
        
        with Gmp(connection, transform=transform) as gmp:
            # Authenticate
            gmp.authenticate(self.username, self.password)
            
            # Create target
            resp = gmp.create_target(
                name=f"Target-{target_ip}",
                hosts=[target_ip]
            )
            target_id = resp.get('id')
            
            # Get default scan config
            configs = gmp.get_scan_configs()
            config_id = None
            for config in configs.xpath('config'):
                if 'Full and fast' in config.find('name').text:
                    config_id = config.get('id')
                    break
            
            if not config_id:
                print("No suitable scan config found")
                return None
            
            # Get scanner
            scanners = gmp.get_scanners()
            scanner_id = scanners.xpath('scanner')[0].get('id')
            
            # Create and start task
            resp = gmp.create_task(
                name=f"Scan-{target_ip}-{datetime.now().strftime('%Y%m%d')}",
                config_id=config_id,
                target_id=target_id,
                scanner_id=scanner_id
            )
            task_id = resp.get('id')
            
            # Start the task
            gmp.start_task(task_id)
            
            # Wait for completion
            while True:
                task = gmp.get_task(task_id)
                status = task.xpath('task/status')[0].text
                if status in ['Done', 'Stopped', 'Interrupted']:
                    break
                time.sleep(30)
            
            # Get results
            results = gmp.get_results(task_id=task_id)
            return self._parse_results(target_ip, results)
    
    def _parse_results(self, target_ip: str, results) -> Dict:
        """Parse OpenVAS scan results"""
        
        vuln_data = {
            'last_seen_ip': target_ip,
            'vulnerability_scan_date': datetime.now(timezone.utc).isoformat(),
            'critical_vulns': 0,
            'high_vulns': 0,
            'medium_vulns': 0,
            'low_vulns': 0,
            'vulnerability_score': 0.0
        }
        
        max_severity = 0.0
        
        for result in results.xpath('result'):
            severity = float(result.find('severity').text or 0)
            
            if severity >= 9.0:
                vuln_data['critical_vulns'] += 1
            elif severity >= 7.0:
                vuln_data['high_vulns'] += 1
            elif severity >= 4.0:
                vuln_data['medium_vulns'] += 1
            else:
                vuln_data['low_vulns'] += 1
            
            max_severity = max(max_severity, severity)
        
        vuln_data['vulnerability_score'] = round(max_severity, 1)
        
        return vuln_data
    
    def scan_all_assets(self) -> Dict:
        """Scan all known assets for vulnerabilities"""
        from snipe_api.services.crudbase import BaseCRUDService
        
        # Get all assets from Snipe-IT
        asset_service = BaseCRUDService('/api/v1/hardware', 'asset')
        assets = asset_service.get_all()
        
        vuln_updates = []
        
        for asset in assets:
            # Get IP from custom fields
            ip = asset.get('custom_fields', {}).get('last_seen_ip', {}).get('value')
            
            if ip:
                print(f"Scanning {asset.get('name', 'Unknown')} ({ip})...")
                vuln_data = self.scan_target(ip)
                
                if vuln_data:
                    vuln_data['_asset_id'] = asset['id']
                    vuln_updates.append(vuln_data)
        
        # Update assets with vulnerability data
        results = {'updated': 0, 'failed': 0}
        for update in vuln_updates:
            asset_id = update.pop('_asset_id')
            if asset_service.update(asset_id, update):
                results['updated'] += 1
            else:
                results['failed'] += 1
        
        return results

if __name__ == "__main__":
    scanner = OpenVASScanner()
    results = scanner.scan_all_assets()
    print(f"Vulnerability scan complete: {results['updated']} updated, {results['failed']} failed")