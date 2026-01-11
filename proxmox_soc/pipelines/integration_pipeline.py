"""
Integration Pipeline
Orchestrates state → builder → dispatcher flow for each integration.
"""

import os
from typing import Dict, List
from dataclasses import dataclass

from proxmox_soc.asset_engine.asset_resolver import ResolvedAsset
from proxmox_soc.states.base_state import BaseStateManager
from proxmox_soc.builders.base_builder import BasePayloadBuilder, BuildResult
from proxmox_soc.dispatchers.base_dispatcher import BaseDispatcher


@dataclass
class PipelineResult:
    """Result of running a pipeline."""
    created: int
    updated: int
    skipped: int
    failed: int
    integration: str


class IntegrationPipeline:
    """
    Generic pipeline that coordinates state → builder → dispatcher.
    """
    
    def __init__(
        self,
        name: str,
        state: BaseStateManager,
        builder: BasePayloadBuilder,
        dispatcher: BaseDispatcher,
        dry_run: bool = False
    ):
        self.name = name
        self.state = state
        self.builder = builder
        self.dispatcher = dispatcher
        self.dry_run = dry_run
        self.debug = os.getenv(f'{name.upper().replace("-", "_")}_PIPELINE_DEBUG', '0') == '1'
    
    def process(self, assets: List[ResolvedAsset]) -> PipelineResult:
        """Process assets through the pipeline."""
        results = {'created': 0, 'updated': 0, 'skipped': 0, 'failed': 0}
        to_dispatch: List[tuple] = []
        
        print(f"\n[{self.name}] Processing {len(assets)} assets...")
        
        # Phase 1: State Check + Build
        for asset in assets:
            state_result = self.state.check(asset.canonical_data)
            
            if state_result.action == 'skip':
                results['skipped'] += 1
                if self.debug:
                    print(f"  ─ Skip: {asset.canonical_data.get('name')} ({state_result.reason})")
                continue
            
            try:
                build_result = self.builder.build(asset.canonical_data, state_result)
                to_dispatch.append((asset, state_result, build_result))
                
                if self.debug:
                    symbol = "+" if state_result.action == 'create' else "↻"
                    print(f"  {symbol} {state_result.action}: {asset.canonical_data.get('name')}")
                
            except Exception as e:
                results['failed'] += 1
                if self.debug:
                    print(f"  ✗ Build failed: {asset.canonical_data.get('name')} - {e}")
        
        # Phase 2: Dispatch (unless dry run)
        if self.dry_run:
            print(f"[{self.name}] DRY RUN - Would dispatch {len(to_dispatch)} assets")
            for _, state_result, _ in to_dispatch:
                if state_result.action == 'create':
                    results['created'] += 1
                else:
                    results['updated'] += 1
        else:
            build_results = [br for _, _, br in to_dispatch]
            if build_results:
                dispatch_results = self.dispatcher.sync(build_results)
                results['created'] = dispatch_results.get('created', 0)
                results['updated'] = dispatch_results.get('updated', 0)
                results['failed'] += dispatch_results.get('failed', 0)
            
            # Phase 3: Record state for successful dispatches
            for asset, state_result, build_result in to_dispatch:
                self.state.record(
                    state_result.asset_id,
                    asset.canonical_data,
                    state_result.action
                )
        
        # Save state if applicable (e.g., Wazuh file-based state)
        if hasattr(self.state, 'save'):
            self.state.save()
        
        self._print_summary(results)
        
        return PipelineResult(
            created=results['created'],
            updated=results['updated'],
            skipped=results['skipped'],
            failed=results['failed'],
            integration=self.name
        )
    
    def _print_summary(self, results: Dict):
        mode = "[DRY RUN] " if self.dry_run else ""
        print(f"[{self.name}] {mode}Complete: "
              f"{results['created']} created, "
              f"{results['updated']} updated, "
              f"{results['skipped']} skipped, "
              f"{results['failed']} failed")