import networkx as nx
from pathlib import Path
from typing import List, Dict, Tuple, Union
import os
from Network.network_components import Node, Host, Edge

TOPOLOGY_ZOO_PATH = Path('/home/philip/pd-fastdata/LCDN/Topologies/TZ_full/')


def get_k_smallest_topologies(k: int) -> List[str]:
    all_nx_topos = {}

    for topo in TOPOLOGY_ZOO_PATH.iterdir():
        graph = nx.read_graphml(topo)
        all_nx_topos[topo.name] = graph

    sorted_topologies = dict(
        sorted(all_nx_topos.items(), key=lambda item: (item[1].number_of_nodes(), item[1].number_of_edges()))
    )

    result_list = []

    for key, graph in sorted_topologies.items():
        result_list.append(key)
        print(f'{key}, {graph.number_of_nodes()}, {graph.number_of_edges()}')
        k -= 1

        if k == 0:
            break

    return result_list


def copy_topos(topologies: List[str]):
    for topo in topologies:
        os.system(f'cp {TOPOLOGY_ZOO_PATH/topo} /home/philip/pd-fastdata/LCDN/Topologies/TZ_small/{topo}')


class LCDNTestTopology(object):
    def __init__(self, topology_path: Path, hosts_per_node: int):
        self._topo = nx.read_graphml(topology_path)
        self._name = topology_path.name
        self._hosts_per_node = hosts_per_node
        self._nodes = []
        self._hosts = []
        self._edges = []
        self._last_id = 0

        self._generate_nodes()
        self._generate_hosts()
        self._generate_edges()

    def _generate_nodes(self):
        nodes = list(self._topo.nodes)

        for node in nodes:
            self._nodes.append(Node(f'Switch {node}', self._last_id))
            self._last_id += 1

    def _generate_hosts(self):
        nodes = list(self._topo.nodes)

        for node in nodes:
            for i in range(self._hosts_per_node):
                self._hosts.append(Host(
                    host_id=self._last_id,
                    host_name=f'Host {self._last_id}',
                    mac_address=f'00:00:00:00:00:{self._last_id}',
                    ip_address=f'10.0.0.{self._last_id}',
                    connected_switch=int(node),
                    host_buffer=100000 * 8,
                    switch_buffer=125000 * 8,
                    prop_delay= 7.65 / 1e6,
                    rate=1e9))

                self._last_id += 1

    def _generate_edges(self):
        edges = list(self._topo.edges)

        for edge in edges:
            self._edges.append(Edge(int(edge[0]), int(edge[1]), self._last_id, 1e9, 7.65/1e6, 125000*8))
            self._last_id += 1

    def get_nodes(self):
        return self._nodes

    def get_hosts(self):
        return self._hosts

    def get_edges(self):
        return self._edges


if __name__ == '__main__':
    get_k_smallest_topologies(150)
    #topo = LCDNTestTopology(Path('/home/philip/pd-fastdata/LCDN/Topologies/TZ_small/Basnet.graphml'), 4)
    print('Hello')
