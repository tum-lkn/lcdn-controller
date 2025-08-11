import logging
from typing import List, Dict
import networkx as nx
import time

from Network.network_components import Edge, Node, Host, NetworkManager
from Routing.routing import RoutingModule, FlowRequest, FlowManager, RerouteStrategy, LCDNStrategy, LCDNStrategy

logger = logging.getLogger(__name__)
FORMAT = '%(asctime)s %(levelname)s:%(name)s: %(message)s'


class LCDN(object):
    def __init__(self, logfile: str = 'LCDN.log'):
        logging.basicConfig(filename=logfile, level=logging.DEBUG, format=FORMAT, filemode='w')
        logger.info('LCDN-Manager started')
        self._network_manager= NetworkManager()
        self._flow_manager = FlowManager()

    """ Function to change the Graph """
    def add_node(self, node: Node) -> bool:
        return self._network_manager.add_node(node)

    def add_edge(self, edge: Edge) -> bool:
        return self._network_manager.add_edge(edge)

    def add_host(self, host: Host) -> bool:
        return self._network_manager.add_host(host)

    def remove_node(self, node_id: int) -> bool:
        return self._network_manager.remove_node(node_id)

    def remove_edge(self, edge_id: int) -> bool:
        return self._network_manager.remove_edge(edge_id)

    def remove_host(self, host_id: int) -> bool:
        return self._network_manager.remove_host(host_id)

    """ Functions to embed and manage flows """
    def embed_flow(self, flow_request: FlowRequest):
        """ Returns FlowAdmission or None

        """

        # Check if we have hosts in the endpoints
        if not self._network_manager.is_node_host(flow_request.sourceVM):
            logger.error('Source is not a Host.')
            return None

        if not self._network_manager.is_node_host(flow_request.destinationVM):
            logger.error('Destination is not a Host.')
            return None

        # Try to embed the Flow
        start_ns = time.time_ns()
        embedding, networks, rerouted_flows = self._flow_manager.embed_new_flow(flow_request, self._network_manager.get_current_networks())
        stop_ns = time.time_ns()

        if embedding is not None:
            self._network_manager.update_network_state(networks)
            # get reroute results
            rerouted_flows_returnable = []
            if rerouted_flows != None:
                for r_flow in rerouted_flows:
                    rerouted_flows_returnable.append({
                        "id": r_flow.id,
                        "path":r_flow.path,
                        "priority": r_flow.priority
                    })

            logger.info(f'Found Path for Flow: {embedding.path} with priority {embedding.priority}')
            flow_admission = {
                "id": embedding.id,
                "src": flow_request.sourceVM,
                "dst": flow_request.destinationVM,
                "path": embedding.path,
                "priority": embedding.priority,
                "embedding_strategy": str(self._flow_manager._strategy),
                "embedding_time": stop_ns - start_ns,
                "rerouted_flows": rerouted_flows_returnable
            }
            return flow_admission
        else:
            return None

    def get_all_flows_with_information(self):
        return self._flow_manager.get_all_flows()
    
    def remove_flow(self, flow_id):
        networks = self._flow_manager.remove_flow(flow_id, self._network_manager.get_current_networks())
        self._network_manager.update_network_state(networks)

    """ Functions to set parameters to set routing """
    def set_rerouting_strategy(self, strategy: RerouteStrategy):
        self._flow_manager.set_reroute_strat(strategy)

    def set_initial_sps(self, k_sps: int) -> bool:
        self._flow_manager.set_init_ksp(k_sps)
        return True

    def set_reroutings(self, reroutes: int) -> bool:
        self._flow_manager.set_reroutes(reroutes)

    def set_ksp_offset(self, offset: int) -> bool:
        self._flow_manager.set_ksp_offset(offset)

    def set_initial_q_level(self, q_level: int) -> bool:
        self._flow_manager.set_first_queue(q_level)

    def set_lcdn_strategy(self, strategy: LCDNStrategy) -> bool:
        self._flow_manager.set_strategy(strategy)
        return True

    def set_greedy_probability(self, p: float) -> bool:
        self._flow_manager.set_greedy_p(p)
        return True

    """ Debug and ease of use Functions """
    def get_node_id_from_ip(self):
        self._network_manager.get_id_from_ip(ip)
        return node_id 

    def get_number_of_reroutes(self) -> int:
        return self._flow_manager.get_number_of_reroutes()

    def get_delay_of_flow(self, flow_id: int) -> float:
        return self._flow_manager.get_delay_of_flow(flow_id, self._network_manager.get_current_networks())

    def get_all_q_delays(self):
        return self._network_manager.get_all_delays()

    def get_all_buffers(self):
        return self._network_manager.get_all_buffers()
    
    def get_all_rates(self):
        return self._network_manager.get_all_rates()
    
    def draw_q_delay(self):
        self._network_manager.get_current_networks()[0].draw_q_delay()
        self._network_manager.get_current_networks()[1].draw_q_delay()
        self._network_manager.get_current_networks()[2].draw_q_delay()
        self._network_manager.get_current_networks()[3].draw_q_delay()

    def draw_burst(self):
        self._network_manager.get_current_networks()[0].draw_burst()
        self._network_manager.get_current_networks()[1].draw_burst()
        self._network_manager.get_current_networks()[2].draw_burst()
        self._network_manager.get_current_networks()[3].draw_burst()

    def draw_rate(self):
        self._network_manager.get_current_networks()[0].draw_rate()
        self._network_manager.get_current_networks()[1].draw_rate()
        self._network_manager.get_current_networks()[2].draw_rate()
        self._network_manager.get_current_networks()[3].draw_rate()


if __name__ == '__main__':
    n1 = Node('node1', 1)
    n2 = Node('node2', 2)
    n3 = Node('node3', 3)

    l1 = Edge(1, 2, 1, 1e9 / 8, 0.0, 970000)
    l2 = Edge(2, 3, 2, 1e9 / 8, 0.0, 970000)
    l3 = Edge(1, 3, 3, 1e9 / 8, 0.0, 970000)

    h1 = Host(host_id=4,
              host_name='host1',
              mac_address='00:00:00:00:00:01',
              ip_address='10.0.0.1',
              connected_switch=1,
              host_buffer=970000,
              switch_buffer=970000,
              prop_delay=0.0,
              rate=1e9 / 8)

    h2 = Host(host_id=5,
              host_name='host2',
              mac_address='00:00:00:00:00:02',
              ip_address='10.0.0.2',
              connected_switch=2,
              host_buffer=970000,
              switch_buffer=970000,
              prop_delay=0.0,
              rate=1e9 / 8)

    lcdn = LCDN()
    lcdn.add_node(n1)
    lcdn.add_node(n2)
    lcdn.add_node(n3)
    lcdn.add_edge(l1)
    lcdn.add_edge(l2)
    lcdn.add_edge(l3)
    lcdn.add_host(h1)
    lcdn.add_host(h2)

    f1 = FlowRequest(4, 5, 69, 70, 25e6, 150.0/1e3)
    f2 = FlowRequest(4, 5, 70, 80, 25e6, 50.0/1e3)
    f3 = FlowRequest(4, 5, 71, 60, 100000, 1.8/1e3)

    path_sol = lcdn.embed_flow(f1)

    # lcdn.draw_q_delay()

    print(path_sol)
    path_sol = lcdn.embed_flow(f2)
    print(path_sol)

    # lcdn.draw_q_delay()

    path_sol = lcdn.embed_flow(f3)
    print(path_sol)

    #lcdn.draw_q_delay()
    #lcdn.draw_rate()
    lcdn.draw_burst()
