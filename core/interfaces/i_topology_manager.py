from abc import ABC, abstractmethod
from typing import List, Tuple
import networkx

class ITopologyManager(ABC):
    @abstractmethod
    def add_host(self):
        raise NotImplementedError

    @abstractmethod
    def remove_host(self):
        raise NotImplementedError

    @abstractmethod
    def add_switch(self, name: str = None):
        raise NotImplementedError

    @abstractmethod
    def remove_switch(self):
        raise NotImplementedError

    @abstractmethod
    def add_edge(self):
        raise NotImplementedError

    @abstractmethod
    def remove_edge(self):
        raise NotImplementedError

    @abstractmethod
    def get_networks(self) -> List[networkx.DiGraph]:
        """Return all network layers"""
        raise NotImplementedError

    @abstractmethod
    def get_nodes(self) -> List[str]:
        """Return list of nodes."""
        raise NotImplementedError

    @abstractmethod
    def get_edges(self) -> List[Tuple[str, str]]:
        """Return list of edges."""
        raise NotImplementedError
