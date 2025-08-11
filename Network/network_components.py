from __future__ import annotations
import json
import copy
from typing import List, Dict, Tuple
import logging
import networkx as nx
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from dataclasses import dataclass
import math

from NetworkCalculus.arrival_curve import ArrivalCurve
from NetworkCalculus.service_curve import ServiceCurve

logger = logging.getLogger(__name__)
logging.getLogger('matplotlib').setLevel(logging.WARNING)

MAX_PACKET_SIZE_DELAY = 24.48 / 1e6


@dataclass
class Node:
    name: str
    node_id: int


@dataclass
class Edge:
    first_node: int
    second_node: int
    link_id: int
    rate: float
    prop_delay: float
    q_size: float


@dataclass
class Host:
    host_id: int
    host_name: str
    mac_address: str
    ip_address: str
    connected_switch: int
    host_buffer: float
    switch_buffer: float
    prop_delay: float
    rate: float


class Network(object):
    def __init__(self, priority, threshold):
        logger.debug('Network Module created.')
        self._graph = nx.DiGraph()
        self._priority = priority
        self._threshold = threshold

        # Housekeeping Variables
        self._nodes = {}
        self._edges = {}
        self._hosts = {}

    def get_priority(self):
        return self._priority

    def get_threshold(self):
        return self._threshold

    def get_id_from_ip(self, ip: str) -> int:
        for node_id, host in self._hosts.items():
            if host.ip_address == ip:
                return node_id
    
    def add_node(self, node: Node) -> bool:
        logger.info(f'Adding new node {node.node_id}')
        logger.debug(f'Parameters: {node}')
        self._nodes[node.node_id] = node

        self._graph.add_node(node.node_id, name=node.name, type="node")

        return True

    def remove_node(self, node_id: int) -> bool:
        logger.info(f'Removing node {node_id}')
        node = self._nodes[node_id]
        self._nodes.pop(node.node_id)
        self._graph.remove_node(node.node_id)

        return True

    def add_edge(self, edge: Edge) -> bool:
        logger.info(f'Adding new edge {edge.first_node} {edge.second_node}')
        logger.debug(f'Parameters: {edge}')
        self._edges[edge.link_id] = edge

        self._graph.add_edge(edge.first_node, edge.second_node,
                             link_id=edge.link_id,
                             rate=edge.rate,
                             prop_delay=edge.prop_delay,
                             buffer=edge.q_size,
                             threshold=self._threshold,
                             cost=1.0,
                             q_delay=0.0,
                             arrival_curve=ArrivalCurve(rate=0.0, burst=0.0),
                             service_curve=ServiceCurve(latency=edge.prop_delay + MAX_PACKET_SIZE_DELAY, rate=edge.rate))

        self._graph.add_edge(edge.second_node, edge.first_node,
                             link_id=edge.link_id,
                             rate=edge.rate,
                             prop_delay=edge.prop_delay,
                             buffer=edge.q_size,
                             threshold=self._threshold,
                             cost=1.0,
                             q_delay=0.0,
                             arrival_curve=ArrivalCurve(rate=0.0, burst=0.0),
                             service_curve=ServiceCurve(latency=edge.prop_delay + MAX_PACKET_SIZE_DELAY, rate=edge.rate))

        return True

    def remove_edge(self, edge_id: int) -> bool:
        logger.info(f'Removing edge {edge_id}')
        edge = self._edges[edge_id]
        logger.debug(f'Parameters: {edge}')

        self._edges.pop(edge.link_id)

        self._graph.remove_edge(edge.first_node, edge.second_node)
        self._graph.remove_edge(edge.second_node, edge.first_node)

        return True

    def add_host(self, host: Host) -> bool:
        logger.info(f'Adding new host {host.host_id}')
        logger.debug(f'Parameters: {host}')
        self._hosts[host.host_id] = host

        self._graph.add_node(host.host_id, name=host.host_name, type="host")

        # Add Connections
        self._graph.add_edge(host.host_id, host.connected_switch,
                             rate=host.rate,
                             prop_delay=host.prop_delay,
                             buffer=host.host_buffer,
                             threshold=self._threshold,
                             cost=1.0,
                             q_delay=0.0,
                             arrival_curve=ArrivalCurve(rate=0.0, burst=0.0),
                             service_curve=ServiceCurve(latency=MAX_PACKET_SIZE_DELAY, rate=host.rate))

        self._graph.add_edge(host.connected_switch, host.host_id,
                             rate=host.rate,
                             prop_delay=host.prop_delay,
                             buffer=host.switch_buffer,
                             threshold=self._threshold,
                             cost=1.0,
                             q_delay=0.0,
                             arrival_curve=ArrivalCurve(rate=0.0, burst=0.0),
                             service_curve=ServiceCurve(latency=host.prop_delay + MAX_PACKET_SIZE_DELAY, rate=host.rate))

        return True

    def remove_host(self, host_id: int) -> bool:
        logger.info(f'Removing host {host_id}')
        host = self._hosts[host_id]
        self._hosts.pop(host.host_id)

        self._graph.remove_node(host.host_id)
        self._graph.remove_edge(host.connected_switch, host.host_id)
        self._graph.remove_edge(host.host_id, host.connected_switch)

        return True

    def get_network_graph(self):
        return self._graph

    def is_host(self, node_id: int) -> bool:
        is_host = node_id in self._hosts.keys()
        return is_host

    def debug_edge(self, edge):
        ac = nx.get_edge_attributes(self._graph, 'arrival_curve')[edge]
        sc = nx.get_edge_attributes(self._graph, 'service_curve')[edge]
        cost = nx.get_edge_attributes(self._graph, 'cost')[edge]
        buffer = nx.get_edge_attributes(self._graph, 'buffer')[edge]

        print(f'---- Edge: {edge[0]} - {edge[1]} ----')
        print(f'{ac}; {sc}')
        print(f'Threshold: {self._threshold}: Current Usage: {sc.delay(ac)}')
        print(f'Buffer Size: {buffer}; Used: {sc.buffer_chameleon(ac, self._threshold)}')
        print(f'Cost for Routing: {cost}')

    def debug_edge_nc(self, edge):
        ac = nx.get_edge_attributes(self._graph, 'arrival_curve')[edge]
        sc = nx.get_edge_attributes(self._graph, 'service_curve')[edge]

        print(f'Edge: {edge[0]} - {edge[1]}; {ac}; {sc}')

    def debug_all_edges(self):
        for edge in self._graph.edges():
            self.debug_edge(edge)

        print('#####################################################')

    def debug_all_edges_nc(self):
        for edge in self._graph.edges():
            self.debug_edge_nc(edge)

        print('#####################################################')

    def get_all_delays(self) -> Dict[Tuple[int, int], float] :
        all_delays = {}

        acs = nx.get_edge_attributes(self._graph, 'arrival_curve')
        scs = nx.get_edge_attributes(self._graph, 'service_curve')

        for edge in self._graph.edges():
            if self._priority == 0:
                # Include all edges
                all_delays[edge] = scs[edge].delay(acs[edge])
            else:
                if not self.is_host(edge[0]):
                    all_delays[edge] = scs[edge].delay(acs[edge])

        return all_delays

    def get_all_buffers(self) -> Dict[Tuple[int, int], float] :
        all_buffers = {}

        acs = nx.get_edge_attributes(self._graph, 'arrival_curve')
        scs = nx.get_edge_attributes(self._graph, 'service_curve')

        for edge in self._graph.edges():
            if self._priority == 0:
                # Include all edges
                all_buffers[edge] = scs[edge].buffer_chameleon(acs[edge], self._threshold)
            else:
                if not self.is_host(edge[0]):
                    all_buffers[edge] = scs[edge].buffer_chameleon(acs[edge], self._threshold)

        return all_buffers
    
    def get_all_rates(self) -> Dict[Tuple[int, int], float] :
        all_rates = {}
        acs = nx.get_edge_attributes(self._graph, 'arrival_curve')

        for edge in self._graph.edges():
            if self._priority == 0:
                # Include all edges
                all_rates[edge] = acs[edge].rate 
            else:
                if not self.is_host(edge[0]):
                    all_rates[edge] = acs[edge].rate 

        return all_rates

    def draw(self):
        color_map = []
        for node in self._graph.nodes(data=True):
            if node[1]['type'] == 'host':
                color_map.append('skyblue')  # Color for hosts
            elif node[1]['type'] == 'node':
                color_map.append('lightgreen')  # Color for switches

        # Draw the network
        plt.figure(figsize=(8, 6))
        nx.draw(self._graph, with_labels=True, node_color=color_map, node_size=800, font_size=10, font_color='black',
                edge_color='gray', arrowsize=20, connectionstyle='arc3,rad=0.1')
        plt.show()

    def copy(self) -> Network:
        network_copy = Network(self._priority, self._threshold)
        network_copy._graph = copy.deepcopy(self._graph)

        network_copy._nodes = copy.deepcopy(self._nodes)
        network_copy._edges = copy.deepcopy(self._edges)
        network_copy._hosts = copy.deepcopy(self._hosts)

        return network_copy

    def draw_q_delay(self):
        delays = [self._graph[u][v]['q_delay'] for u, v in self._graph.edges()]
        colors = ["lightgreen", "yellow", "red"]
        nodes = [0.0, 0.5, 1.0]
        my_cmap = mcolors.LinearSegmentedColormap.from_list("cmaps", list(zip(nodes, colors)))
        norm = mcolors.Normalize(vmin=0.0, vmax=self._threshold)
        edge_colors = [my_cmap(norm(delay)) for delay in delays]

        color_map = []
        for node in self._graph.nodes(data=True):
            if 'type' not in node[1]:
                print('häääää')
            if node[1]['type'] == 'host':
                color_map.append('skyblue')  # Color for hosts
            elif node[1]['type'] == 'node':
                color_map.append('lightgreen')  # Color for switches

        edge_labels = nx.get_edge_attributes(self._graph, 'q_delay')
        pos = nx.spring_layout(self._graph)
        plt.figure(figsize=(8, 6))
        nx.draw(self._graph, pos=pos, with_labels=True, node_color=color_map, edge_color=edge_colors, width=2,
                arrowsize=20, connectionstyle='arc3,rad=0.2', node_size=800, font_size=10, font_color='black')
        bbox_props = dict(boxstyle="round,pad=0.3", edgecolor='none', facecolor='white', alpha=0.5)
        nx.draw_networkx_edge_labels(self._graph, pos=pos, edge_labels=edge_labels, font_size=10, label_pos=0.7, bbox=bbox_props)

        plt.show()

    def draw_rate(self):
        rates = [self._graph[u][v]['arrival_curve'].rate / self._graph[u][v]['service_curve'].rate for u, v in self._graph.edges()]
        colors = ["lightgreen", "yellow", "red"]
        nodes = [0.0, 0.5, 1.0]
        my_cmap = mcolors.LinearSegmentedColormap.from_list("cmaps", list(zip(nodes, colors)))
        edge_colors = [my_cmap(rate) for rate in rates]

        color_map = []
        for node in self._graph.nodes(data=True):
            if node[1]['type'] == 'host':
                color_map.append('skyblue')  # Color for hosts
            elif node[1]['type'] == 'node':
                color_map.append('lightgreen')  # Color for switches

        edge_labels_raw = nx.get_edge_attributes(self._graph, 'arrival_curve')

        edge_labels = {}
        for edge, ac in edge_labels_raw.items():
            edge_labels[edge] = ac.rate

        pos = nx.spring_layout(self._graph)
        plt.figure(figsize=(8, 6))
        nx.draw(self._graph, pos=pos, with_labels=True, node_color=color_map, edge_color=edge_colors, width=2,
                arrowsize=20, connectionstyle='arc3,rad=0.2', node_size=800, font_size=10, font_color='black')
        bbox_props = dict(boxstyle="round,pad=0.3", edgecolor='none', facecolor='white', alpha=0.5)
        nx.draw_networkx_edge_labels(self._graph, pos=pos, edge_labels=edge_labels, font_size=10, label_pos=0.7, bbox=bbox_props)

        plt.show()

    def draw_burst(self):
        bursts = [self._graph[u][v]['arrival_curve'].burst / self._graph[u][v]['buffer'] for u, v in self._graph.edges()]
        colors = ["lightgreen", "yellow", "red"]
        nodes = [0.0, 0.5, 1.0]
        my_cmap = mcolors.LinearSegmentedColormap.from_list("cmaps", list(zip(nodes, colors)))
        edge_colors = [my_cmap(burst) for burst in bursts]

        color_map = []
        for node in self._graph.nodes(data=True):
            if node[1]['type'] == 'host':
                color_map.append('skyblue')  # Color for hosts
            elif node[1]['type'] == 'node':
                color_map.append('lightgreen')  # Color for switches

        edge_labels_raw = nx.get_edge_attributes(self._graph, 'arrival_curve')

        edge_labels = {}
        for edge, ac in edge_labels_raw.items():
            edge_labels[edge] = ac.burst

        pos = nx.spring_layout(self._graph)
        plt.figure(figsize=(8, 6))
        nx.draw(self._graph, pos=pos, with_labels=True, node_color=color_map, edge_color=edge_colors, width=2,
                arrowsize=20, connectionstyle='arc3,rad=0.2', node_size=800, font_size=10, font_color='black')
        bbox_props = dict(boxstyle="round,pad=0.3", edgecolor='none', facecolor='white', alpha=0.5)
        nx.draw_networkx_edge_labels(self._graph, pos=pos, edge_labels=edge_labels, font_size=10, label_pos=0.7, bbox=bbox_props)

        plt.show()


class NetworkManager(object):
    def __init__(self, num_of_qs: int=4):
        self._q_networks = [] # index is prio
        self._4_q_thresholds = [0.5 / 1e3, 1 / 1e3, 6 / 1e3, 24 / 1e3]
        self._8_q_thresholds = [0.1 / 1e3, 0.5 / 1e3, 1 / 1e3, 3 / 1e3, 6 / 1e3, 12 / 1e3, 18 / 1e3, 24 / 1e3]

        if num_of_qs == 4:
            for i in range(4):
                self._q_networks.append(Network(i, self._4_q_thresholds[i]))
        elif num_of_qs == 8:
            for i in range(8):
                self._q_networks.append(Network(i, self._8_q_thresholds[i]))
        else:
            print('Numbers of Qs musst be 4 or 8 for now')

    def get_current_networks(self) -> List[Network]:
        return self._q_networks

    def update_network_state(self, networks: List[Network]) -> None:
        self._q_networks = copy.deepcopy(networks)

    def is_node_host(self, node_id: int) -> bool:
        return self._q_networks[0].is_host(node_id)

    def get_id_from_ip(self, ip: str):
        node_id = self._q_networks[0].get_id_from_ip(ip)
        return node_id        

    """ Pass Through for add, remove functions """

    def add_node(self, node: Node) -> bool:
        for q_network in self._q_networks:
            q_network.add_node(node)

        return True

    def add_edge(self, edge: Edge) -> bool:
        for q_network in self._q_networks:
            q_network.add_edge(edge)

        return True

    def add_host(self, host: Host) -> bool:
        for q_network in self._q_networks:
            q_network.add_host(host)

        return True

    def remove_node(self, node_id: int) -> bool:
        for q_network in self._q_networks:
            q_network.remove_node(node_id)

        return True

    def remove_edge(self, edge_id: int) -> bool:
        for q_network in self._q_networks:
            q_network.remove_edge(edge_id)

        return True

    def remove_host(self, host_id: int) -> bool:
        for q_network in self._q_networks:
            q_network.remove_host(host_id)

        return True

    def get_all_delays(self) -> Dict[int, Dict[Tuple[int, int], float]]:
        all_delay = {}
        for i, q_network in enumerate(self._q_networks):
            all_delay[i] = q_network.get_all_delays()

        return all_delay

    def get_all_buffers(self) -> Dict[int, Dict[Tuple[int, int], float]]:
        all_buffer = {}
        for i, q_network in enumerate(self._q_networks):
            all_buffer[i] = q_network.get_all_buffers()

        return all_buffer
    
    def get_all_rates(self) -> Dict[int, Dict[Tuple[int, int], float]]:
        all_rate = {}
        for i, q_network in enumerate(self._q_networks):
            all_rate[i] = q_network.get_all_rates()

        return all_rate
