from abc import ABC, abstractmethod

class IFlowDispatcher(ABC):
    """Interface for the Flow Dispatcher."""

    @abstractmethod
    def install_flow(self):
        raise NotImplementedError

    @abstractmethod
    def uninstall_flow(self):
        raise NotImplementedError
