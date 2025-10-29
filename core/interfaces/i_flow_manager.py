from abc import ABC, abstractmethod
from typing import Union
from core.models.flows import Flow, EmbeddedFlow


class IFlowManger(ABC):
    @abstractmethod
    def add_flow(self, flow: Flow) -> Union[None, EmbeddedFlow]:
        """Start the embedding of a new flow."""
        raise NotImplementedError

    @abstractmethod
    def remove_flow(self, flow_id: int):
        """ Interface to remove a embedded flow with its ID"""
        raise NotImplementedError