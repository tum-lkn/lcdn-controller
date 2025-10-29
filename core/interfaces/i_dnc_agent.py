from abc import ABC, abstractmethod
from typing import Union
from core.models.flows import ResourceReservation
from core.models.topology import LCDNTopology
from core.models.violation import Violation

class IDNCAgent(ABC):
    """Interface for the Deterministic Network Calculus Agent."""

    @abstractmethod
    def reserve_resources(self, reservation: ResourceReservation, network: LCDNTopology) -> Union[Violation, LCDNTopology]:
        """Place a resource reservation on the network. Returns a Violation or the Networks with the resource reservation."""
        raise NotImplementedError

    @abstractmethod
    def remove_resources(self, reservation: ResourceReservation, network: LCDNTopology) -> LCDNTopology:
        """Releases a resource reservation on the network. Does not apply residuals"""
        raise NotImplementedError

    @abstractmethod
    def apply_reservations(self, network: LCDNTopology) -> LCDNTopology:
        """Recalculate network state and check for violations, apply residuals ..."""
        raise NotImplementedError
