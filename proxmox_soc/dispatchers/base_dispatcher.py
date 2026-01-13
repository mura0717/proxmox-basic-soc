"""
Abstract base class for all dispatchers.
Ensures every dispatcher implements the 'sync' method.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Union, Any
from proxmox_soc.builders.base_builder import BuildResult

class BaseDispatcher(ABC):
    
    @abstractmethod
    def sync(self, build_results: List[BuildResult]) -> Dict[str, int]:
        """
        Sync built payloads to the destination system.
        
        Args:
            build_results: List of BuildResult objects (output from Builder)
            
        Returns:
            Dictionary with counts e.g. {"created": X, "updated": Y, "failed": Z})
        """
        pass