from abc import ABC, abstractmethod

from core.models.topology import LCDNTopology


class IRoutingManager(ABC):
    @abstractmethod
    def find_shortest_path(self, src: int, dst: int, network: LCDNTopology):
        raise NotImplementedError