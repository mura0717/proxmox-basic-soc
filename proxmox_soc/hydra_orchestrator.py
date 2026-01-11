"""
Main Orchestrator
Coordinates scanners, resolver, and integration pipelines.
"""

import argparse
import sys
from typing import List, Optional
from pathlib import Path

from proxmox_soc.scanners.nmap_scanner import NmapScanner
from proxmox_soc.scanners.ms365_aggregator import Microsoft365Aggregator
from proxmox_soc.asset_engine.asset_resolver import AssetResolver

from proxmox_soc.states.snipe_state import SnipeStateManager
from proxmox_soc.states.wazuh_state import WazuhStateManager
from proxmox_soc.states.zabbix_state import ZabbixStateManager

from proxmox_soc.builders.snipe_builder import SnipePayloadBuilder
from proxmox_soc.builders.wazuh_builder import WazuhPayloadBuilder
from proxmox_soc.builders.zabbix_builder import ZabbixPayloadBuilder

from proxmox_soc.dispatchers.snipe_dispatcher import SnipeDispatcher
from proxmox_soc.dispatchers.wazuh_dispatcher import WazuhDispatcher
from proxmox_soc.dispatchers.zabbix_dispatcher import ZabbixDispatcher

from proxmox_soc.pipelines.integration_pipeline import IntegrationPipeline
from proxmox_soc.config.hydra_settings import WAZUH


class HydraOrchestrator:
    """
    Main entry point for asset synchronization.
    """
    
    def __init__(self, dry_run: bool = False, skip_integrations: Optional[List[str]] = None):
        self.resolver = AssetResolver()
        self.dry_run = dry_run
        self.skip_integrations = skip_integrations or []
        self._pipelines = None
    
    @property
    def pipelines(self):
        """Lazy initialization of pipelines."""
        if self._pipelines is None:
            self._pipelines = self._create_pipelines()
        return self._pipelines
    
    def _create_pipelines(self):
        """Create integration pipelines."""
        return {
            'snipe': IntegrationPipeline(
                name='Snipe-IT',
                state=SnipeStateManager(),
                builder=SnipePayloadBuilder(),
                dispatcher=SnipeDispatcher(),
                dry_run=self.dry_run
            ),
            'wazuh': IntegrationPipeline(
                name='Wazuh',
                state=WazuhStateManager(WAZUH.state_file),
                builder=WazuhPayloadBuilder(),
                dispatcher=WazuhDispatcher(),
                dry_run=self.dry_run
            ),
            'zabbix': IntegrationPipeline(
                name='Zabbix',
                state=ZabbixStateManager(),
                builder=ZabbixPayloadBuilder(),
                dispatcher=ZabbixDispatcher(),
                dry_run=self.dry_run
            ),
        }
    
    def run_full_sync(self, integrations: Optional[List[str]] = None, 
                      sources: Optional[List[str]] = None):
        """Run complete sync across data sources and integrations."""
        
        # Collect from sources
        print("=" * 60)
        print("COLLECTING DATA FROM SOURCES")
        print("=" * 60)
        
        all_resolved = []
        active_sources = sources or ['nmap', 'ms365']
        
        if 'nmap' in active_sources:
            nmap_data = NmapScanner().collect_assets()
            all_resolved.extend(self.resolver.resolve('nmap', nmap_data))
        
        if 'ms365' in active_sources:
            ms365_data = Microsoft365Aggregator().collect_assets()
            all_resolved.extend(self.resolver.resolve('microsoft365', ms365_data))
        
        print(f"\nTotal resolved assets: {len(all_resolved)}")
        
        # Run pipelines
        print("\n" + "=" * 60)
        print("RUNNING INTEGRATION PIPELINES")
        if self.dry_run:
            print("MODE: DRY RUN (no changes will be made)")
        print("=" * 60)
        
        active_integrations = integrations or list(self.pipelines.keys())
        active_integrations = [i for i in active_integrations if i not in self.skip_integrations]
        
        results = {}
        for name in active_integrations:
            if name in self.pipelines:
                results[name] = self.pipelines[name].process(all_resolved)
        
        # Summary
        self._print_final_summary(results)
        
        return results
    
    def _print_final_summary(self, results):
        """Print final summary of all pipelines."""
        print("\n" + "=" * 60)
        print("FINAL SUMMARY")
        print("=" * 60)
        
        total_created = sum(r.created for r in results.values())
        total_updated = sum(r.updated for r in results.values())
        total_skipped = sum(r.skipped for r in results.values())
        total_failed = sum(r.failed for r in results.values())
        
        for name, result in results.items():
            print(f"  {name}: {result.created} created, {result.updated} updated, "
                  f"{result.skipped} skipped, {result.failed} failed")
        
        print(f"\n  TOTAL: {total_created} created, {total_updated} updated, "
              f"{total_skipped} skipped, {total_failed} failed")


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='Hydra Asset Synchronization Pipeline',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Full sync, all sources and integrations
  %(prog)s --dry-run                # Test run, no changes made
  %(prog)s --source nmap            # Only sync nmap data
  %(prog)s --skip-zabbix            # Skip Zabbix integration
  %(prog)s --only snipe wazuh       # Only sync to Snipe-IT and Wazuh
        """
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Run without making any changes'
    )
    
    parser.add_argument(
        '--source', '-s',
        choices=['nmap', 'ms365', 'all'],
        default='all',
        help='Data source to collect from (default: all)'
    )
    
    parser.add_argument(
        '--only', '-o',
        nargs='+',
        choices=['snipe', 'wazuh', 'zabbix'],
        help='Only run specified integrations'
    )
    
    parser.add_argument(
        '--skip-snipe',
        action='store_true',
        help='Skip Snipe-IT integration'
    )
    
    parser.add_argument(
        '--skip-wazuh',
        action='store_true',
        help='Skip Wazuh integration'
    )
    
    parser.add_argument(
        '--skip-zabbix',
        action='store_true',
        help='Skip Zabbix integration'
    )
    
    parser.add_argument(
        '--test',
        action='store_true',
        help='Run in test mode with mock data'
    )
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Build skip list
    skip = []
    if args.skip_snipe:
        skip.append('snipe')
    if args.skip_wazuh:
        skip.append('wazuh')
    if args.skip_zabbix:
        skip.append('zabbix')
    
    # Determine sources
    sources = None
    if args.source != 'all':
        sources = [args.source]
    
    # Determine integrations
    integrations = args.only if args.only else None
    
    # Test mode
    if args.test:
        print("Running in TEST mode with mock data...")
        # Import and run test suite
        from proxmox_soc.debug.tests.test_hydra import main as run_tests
        return run_tests()
    
    # Create and run orchestrator
    orchestrator = HydraOrchestrator(
        dry_run=args.dry_run,
        skip_integrations=skip
    )
    
    orchestrator.run_full_sync(
        integrations=integrations,
        sources=sources
    )
    
    return 0


if __name__ == "__main__":
    sys.exit(main())