"""
Abstract base class for all dispatchers.
Ensures every dispatcher implements the 'sync' method.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any

class BaseDispatcher(ABC):
    
    @abstractmethod
    def sync(self, assets: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Sync assets to the destination system.
        
        Args:
            assets: List of standardized action objects (from AssetMatcher)
            
        Returns:
            Dictionary with counts e.g. {"created": X, "updated": Y, "failed": Z})
        """
        pass