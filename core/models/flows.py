from dataclasses import dataclass
from typing import Tuple, List


@dataclass
class Flow:
    """
    The data type the user provides when a new flow should enter the network.
    Args:
        source_vm (int): the source of the flow. it is the id of the host where the flow starts.
        destination_vm (int): the destination of the flow. it is the id of the host where the flow ends.
        protocol (int): protocol of the flow (uniquely identify flows between source and destination).
        burst: burst size in bits.
        rate: data rate in bits per second.
        deadline: deadline in seconds.
    """
    source_vm: int
    destination_vm: int
    protocol: int
    burst: int
    rate: float
    deadline: float

@dataclass
class EmbeddedFlow:
    """
    The Answer LCDN provides when a flow is embedded in the network.
    Args:
        flow_id (int): the id of the flow.
        path (List[Tuple[int, int]]): List of Network Edges in the Format (Node, Node)
        priority (int): The priority the flow occupies..
    """
    flow_id: int
    path: List[Tuple[int, int]]
    priority: int

@dataclass
class ResourceReservation:
    """
    Encapsules the requirements (rate, burst, deadline, and path) for the DNC Module
    """
    path: List[Tuple[int, int]]
    rate: float
    burst: int
    deadline: float

@dataclass
class InternalFlow:
    """
    Internal Handler for flow life cycle management.
    Args:
        flow_id (int): the id of the flow.
    """
    flow_id: int
    flow_request: Flow
    reservation: ResourceReservation