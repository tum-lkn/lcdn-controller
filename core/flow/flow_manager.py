from core.interfaces.i_flow_manager import IFlowManger
from core.models.flows import Flow


class FlowManager(IFlowManger):
    def __init__(self):
        self._flows = {}
        self._last_flow_id = 0

    def add_flow(self, flow: Flow):
        """Add a new flow to the network. LCDN checks if it can be fitted into the network"""
        pass

    def remove_flow(self, flow_id: int):
        pass