from abc import ABC, abstractmethod

class BaseDispatcher(ABC):
    @abstractmethod
    def sync(self, assets: list):
        """Takes the list of standardized assets and syncs to destination"""
        pass