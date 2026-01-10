"""
Base Payload Builder Interface
Defines the contract for all integration payload builders.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Dict, Optional, Any

from proxmox_soc.states.base_state import StateResult


@dataclass
class BuildResult:
    """Result of payload building."""
    payload: Dict[str, Any]  # The built payload
    asset_id: str           # Reference back to state
    action: str             # 'create' or 'update'
    metadata: Dict          # Additional context


class BasePayloadBuilder(ABC):
    """
    Abstract base for integration payload builders.
    
    Responsibilities:
    - Transform canonical data to integration-specific format
    - Merge with existing data when updating
    - Pure transformation - no side effects
    """
    
    @abstractmethod
    def build(self, asset_data: Dict, state_result: StateResult) -> BuildResult:
        """
        Build payload for target integration.
        
        Args:
            asset_data: Canonical asset data from resolver
            state_result: Result from state manager (action, existing data)
            
        Returns:
            BuildResult with payload and metadata
        """
        pass