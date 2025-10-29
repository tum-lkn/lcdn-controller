from dataclasses import dataclass
from typing import List
import networkx


@dataclass
class Edge:
    """ Model representing a edge in the topology"""
    edge_id: int
    first_node_id: int
    second_node_id: int
    link_rate: float
    delay: float
    q_size: float
    threshold: float


@dataclass
class Switch:
    node_id: int
    switch_name: int


@dataclass
class Host:
    """
    Model representing a host in the topology. A Host can send or receive data.
    Args:

    """
    node_id: int
    host_name: str
    mac_address: str
    ip_address: str
    connected_switch: int
    host_buffer: float
    switch_buffer: float
    prop_delay: float
    rate: float

# LCDN Topology consists of P Networks

@dataclass
class LCDNTopology:
    networks: List[networkx.DiGraph]
    thresholds: List[float]