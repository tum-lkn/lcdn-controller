import copy
from dataclasses import dataclass
from typing import List, Tuple, Union, Dict
import networkx as nx
import logging
from enum import Enum
import time
from itertools import islice
import numpy as np

from Network.network_components import Network
from NetworkCalculus.arrival_curve import ArrivalCurve
from NetworkCalculus.dnc import DNCAgent, ResourceReservation, Violation


logger = logging.getLogger(__name__)


class RerouteStrategy(Enum):
    SINGLE_FLOW = 1
    COMPOUND_FLOWS = 2

class LCDNStrategy(Enum):
    GREEDY = 1
    NOTGREEDY = 2
    GREEDYMIX = 3

@dataclass
class FlowRequest:
    sourceVM: int
    destinationVM: int
    protocol: int
    burst: int
    rate: float
    deadline: float

@dataclass
class EmbeddedFlow:
    id: int
    flow_request: FlowRequest
    flow_reservation: ResourceReservation
    path: List[Tuple[int, int]]
    priority: int


@dataclass
class EmbeddingRequest:
    flow: FlowRequest
    path: List[int]
    network: Network


class RoutingModule(object):
    def __init__(self):
        self._network = None
        self._all_networks = []
        self._ksp_offset = 0

    def set_ksp_offset(self, offset: int):
        self._ksp_offset = offset

    def update_network(self, network: nx.DiGraph) -> None:
        self._network = network

    def update_all_networks(self, networks: List[Network]) -> None:
        for network in networks:
            self._all_networks.append(network.get_network_graph())

    @staticmethod    
    def sorted_flow_list_by_edges(all_flows_dict, new_flow_path: List[Tuple[int, int]]):
        result = {}
        set_new_flwo = set(new_flow_path)
        all_flow_paths = {}
        for flow_id, flow_e in all_flows_dict.items():
            all_flow_paths[flow_id] = flow_e.path

        for f_id, e_flow in all_flow_paths.items():
            set_a = set(e_flow)
            result[f_id] = len(set_a & set_new_flwo)
        # Should return a List of the Flow IDs in order of the most common edges
        sorted_flows = sorted(result, key=lambda k: result[k], reverse=True)

        return sorted_flows

    @staticmethod
    def get_edges_from_node_list(path: List[int]) -> List[Tuple[int, int]]:
        edges = []

        for i, node in enumerate(path):
            if i < len(path) - 1:
                edges.append((node, path[i + 1]))

        return edges

    def get_shortest_path(self, src: int, dst: int) -> Union[None, List[List[Tuple[int, int]]]]:
        if self._network is None:
            logger.critical('No Network has been initialized.')
            return None

        # Get up-to-date shortest path based on queue delay
        shortest_path = nx.shortest_path(self._network, source=src, target=dst, weight='cost')

        k_shortest_paths = list(islice(nx.shortest_simple_paths(self._network, source=src, target=dst, weight='cost'), 10))

        shortest_path_length = nx.shortest_path_length(self._network, source=src, target=dst, weight='cost')

        k_shortest_edge_paths = []
        for s_path in k_shortest_paths:
            k_shortest_edge_paths.append(self.get_edges_from_node_list(s_path))

        # TODO: Remove TMP Return
        tmp_return = None

        if len(k_shortest_edge_paths) <= self._ksp_offset:
            tmp_return =  [k_shortest_edge_paths[-1]]
        else:
            tmp_return =  k_shortest_edge_paths[self._ksp_offset:]

        logger.debug(f'SP return {tmp_return}')
        return tmp_return


class FlowManager(object):
    def __init__(self):
        self._test = 0
        self._reroutes = 10
        self._routing = RoutingModule()
        self._dnc = DNCAgent()
        self._all_flows = {}
        self._last_flow_id = 1
        self._init_ksp = 1
        self._flow_reroutes = 0
        self._first_queue = 0
        self._reroute_strat = RerouteStrategy.SINGLE_FLOW
        self._strategy = LCDNStrategy.GREEDY
        self._is_greedy_mix = False
        self._greedy_p = 1.0

    def set_reroute_strat(self, strategy: RerouteStrategy):
        self._reroute_strat = strategy

    def set_strategy(self, strategy: LCDNStrategy):
        self._strategy = strategy
        if self._strategy == LCDNStrategy.GREEDYMIX:
            self._is_greedy_mix = True

    def set_greedy_p(self, p: float):
        self._greedy_p = p

    def set_init_ksp(self, ksp: int):
        self._init_ksp = ksp

    def set_reroutes(self, reroutes: int):
        self._reroutes = reroutes

    def set_ksp_offset(self, offset: int):
        self._routing.set_ksp_offset(offset)

    def set_first_queue(self, q_level: int):
        self._first_queue = q_level
        
    def get_number_of_reroutes(self):
        return self._flow_reroutes

    def get_all_flows(self):
        all_flows = []
        for key, flow in self._all_flows.items():
            all_flows.append({"id": flow.id, "embed_time": 0, "path": flow.path, "priority": flow.priority, "src": flow.flow_request.sourceVM, "dst": flow.flow_request.destinationVM})
        return all_flows

    def get_delay_of_flow(self, flow_id: int, networks: List[Network]) -> float:
        if not flow_id in self._all_flows:
            logger.error(f'Delay Request: Flow with ID {flow_id} does not exist')
            return 0.0

        path = self._all_flows[flow_id].path
        priority = self._all_flows[flow_id].priority

        delay_q = nx.get_edge_attributes(networks[priority].get_network_graph(), 'q_delay')
        delay_host = nx.get_edge_attributes(networks[0].get_network_graph(), 'q_delay')

        flow_delay = 0.0

        for i, edge in enumerate(path):
            if i == 0:
                flow_delay += delay_host[edge]
            else:
                flow_delay += delay_q[edge]

        return flow_delay

    def embed_new_flow(self, flow: FlowRequest, network: List[Network]) -> Tuple[Union[None, EmbeddedFlow], List[Network], List[EmbeddedFlow]]:
        # Update with the current highest priority network
        self._routing.update_network(network[0].get_network_graph())

        # If we use the mix strategy, we randomly sample which strat to use based on p_greedy
        if self._is_greedy_mix:
            strategy_for_flow = np.random.choice([LCDNStrategy.GREEDY, LCDNStrategy.NOTGREEDY], p=[self._greedy_p, 1 - self._greedy_p])
            self._strategy = strategy_for_flow

        # Get Source and Destination Nodes
        source = flow.sourceVM
        destination = flow.destinationVM
        logger.info(f'Flow Request from {source} to {destination} with {flow.rate} Bps, {flow.burst} Bits, {flow.deadline}s. Looking for path')

        # Find the shortest path based on cost (1 + 1e6 * q_delay)
        shortest_paths = self._routing.get_shortest_path(source, destination)


        if shortest_paths is None:
            logger.info('No Path exists between Source and Destination!')
            return None, network, None

        if len(shortest_paths) == 0:
            logger.info('No Path exists between Source and Destination!')
            return None, network, None

        # Store Network State before Embedding
        clean_network = copy.deepcopy(network)
        found_path = False
        embed_result = None

        # Embed on the first Queue on the shortest path when greedy:
        if self._strategy == LCDNStrategy.GREEDY:
            for i in range(min(len(shortest_paths), self._init_ksp)): 
                embed_result, network_with_new_flow = self.embed_flow_on_path(flow, shortest_paths[i], self._first_queue, network)

                if type(embed_result) is Violation:
                    logger.error(f'Flow could not be embedded on shortest path. Checking next shortest path (if any exist).')
                else:
                    found_path = True
                    break
        # Embed on the shortest path in the lowest queue it still fits
        elif self._strategy == LCDNStrategy.NOTGREEDY:
            queues = [i for i in range(len(network))]
            queues.reverse()
            for i in range(min(len(shortest_paths), self._init_ksp)): 
                # Go through all the qs from the back
                for queue in queues:
                    embed_result, network_with_new_flow = self.embed_flow_on_path(flow, shortest_paths[i], queue, network)

                    if type(embed_result) is Violation:
                        logger.error(f'Flow could not be embedded on shortest path. Checking next shortest path (if any exist).')
                    else:
                        found_path = True
                        break

        if found_path:
            # Successful embedding, no rerouting required.
            return embed_result, network_with_new_flow, None
        else:
            if self._reroutes == 0:
                return None, clean_network, None    
            # Rerouting required
            # Reserve resources for the new flow again. Start with clean network again
            # Rerouting for Greedy Embed Strategy:
            reservation = ResourceReservation(burst=flow.burst,
                                              rate=flow.rate,
                                              deadline=flow.deadline,
                                              path=shortest_paths[0])
            reroute_network = copy.deepcopy(clean_network)
            sorted_flows = self._routing.sorted_flow_list_by_edges(self._all_flows, shortest_paths[0])

            if self._strategy == LCDNStrategy.GREEDY: 
                if self._reroute_strat == RerouteStrategy.SINGLE_FLOW:
                    logger.debug(f'--- Rerouting (Greedy, single flow) ---')
                    # place new flow request into the network
                    self._dnc.reserve_resources(reservation, reroute_network, 0)
                    # Make Checkpoint Network with New Flow Reservation:
                    reroute_with_flow_reservation = copy.deepcopy(reroute_network)

                    # go through candidate flows and embed 1 Q lower. Rerouting only stays if 
                    for i in range(min(len(sorted_flows), self._reroutes)):
                        logger.debug(f'Reroute {i} with {sorted_flows[i]} of {len(sorted_flows)}')
                        net_to_check_reroute = copy.deepcopy(reroute_with_flow_reservation)
                        success, network_with_reroute = self.reroute_embedded_flow(sorted_flows[i], net_to_check_reroute)

                        # If we found a valid embedding, we can return it
                        if success:
                            logger.info(f'Found valid reroute with Flow {sorted_flows[i]}')
                            # Add new flow to List of all Flows
                            logger.info(f'Flow {self._last_flow_id} is now embedded')
                            new_flow_embedding = EmbeddedFlow(self._last_flow_id, flow, reservation, shortest_paths[0], 0)
                            self._all_flows[self._last_flow_id] = new_flow_embedding
                            self._last_flow_id += 1

                            # Increase reroute Counter
                            self._flow_reroutes += 1
                            return new_flow_embedding, network_with_reroute, [self._all_flows[sorted_flows[i]]]

                elif self._reroute_strat == RerouteStrategy.COMPOUND_FLOWS:
                    # Instead of one by one rerouting, we compound the rerouting
                    logger.debug(f'--- Rerouting (Greedy, coumpound flows) ---')
                    compound_net = copy.deepcopy(reroute_network)
                    # Reroute the Candidate Flow and check if it fits
                    rerouted_flows = []
                    for i in range(min(len(sorted_flows), self._reroutes)):
                        logger.debug(f'Reroute {i} with {sorted_flows[i]} of {len(sorted_flows)}')
                        success, compound_net = self.reroute_embedded_flow(sorted_flows[i], compound_net)

                        if success:
                            logger.debug(f'Flow {sorted_flows[i]} is rerouted, Checking if the flow fits')
                            rerouted_flows.append(self._all_flows[sorted_flows[i]])
                            self._flow_reroutes += 1
                            result, compound_net = self.embed_flow_on_path(flow, shortest_paths[0], 0, compound_net)
                            
                            if type(result) is Violation:
                                logger.debug(f'New Flow could not be embedded yet.')
                            else: 
                                # Flow Embeddign for new Flow worked
                                logger.info(f'Flow {self._last_flow_id} is now embedded')
                                return result, compound_net, rerouted_flows

                        else:
                            logger.debug(f'Flow {sorted_flows[i]} could not be rerouted.')


            elif self._strategy == LCDNStrategy.NOTGREEDY:
                if self._reroute_strat == RerouteStrategy.SINGLE_FLOW:
                    logger.debug(f'--- Rerouting (Not Greedy, single flow) ---')

                    self._dnc.reserve_resources(reservation, reroute_network, 0)
                    reroute_with_flow_reservation = copy.deepcopy(reroute_network)

                    # go through candidate flows and embed 1 Q lower. Rerouting only stays if 
                    for i in range(min(len(sorted_flows), self._reroutes)):
                        logger.debug(f'Reroute {i} with {sorted_flows[i]} of {len(sorted_flows)}')
                        success, reroute_with_flow_reservation = self.reroute_embedded_flow(sorted_flows[i], reroute_with_flow_reservation)

                        # If we found a valid embedding, we can return it
                        if success:
                            logger.info(f'Found valid reroute with Flow {sorted_flows[i]}')
                            # Add new flow to List of all Flows
                            logger.info(f'Flow {self._last_flow_id} is now embedded')
                            new_flow_embedding = EmbeddedFlow(self._last_flow_id, flow, reservation, shortest_paths[0], 0)
                            self._all_flows[self._last_flow_id] = new_flow_embedding
                            self._last_flow_id += 1

                            # Increase reroute Counter
                            self._flow_reroutes += 1
                            return new_flow_embedding, reroute_with_flow_reservation, [self._all_flows[sorted_flows[i]]]

                elif self._reroute_strat == RerouteStrategy.COMPOUND_FLOWS:
                    # Instead of one by one rerouting, we compound the rerouting
                    logger.debug(f'--- Rerouting (Not Greedy, coumpound flows) ---')
                    compound_net = copy.deepcopy(reroute_network)
                    # Reroute the Candidate Flow and check if it fits
                    rerouted_flows = []
                    for i in range(min(len(sorted_flows), self._reroutes)):
                        logger.debug(f'Reroute {i} with {sorted_flows[i]} of {len(sorted_flows)}')
                        success, compound_net = self.reroute_embedded_flow(sorted_flows[i], compound_net)

                        if success:
                            logger.debug(f'Flow {sorted_flows[i]} is rerouted, Checking if the flow fits')
                            rerouted_flows.append(self._all_flows[sorted_flows[i]])
                            self._flow_reroutes += 1
                            result, compound_net = self.embed_flow_on_path(flow, shortest_paths[0], 0, compound_net)
                            
                            if type(result) is Violation:
                                logger.debug(f'New Flow could not be embedded yet.')
                            else: 
                                # Flow Embeddign for new Flow worked
                                logger.info(f'Flow {self._last_flow_id} is now embedded')
                                return result, compound_net, rerouted_flows

                        else:
                            logger.debug(f'Flow {sorted_flows[i]} could not be rerouted.')

            #  reroute_network = copy.deepcopy(clean_network)
          #  reservation = ResourceReservation(burst=flow.burst,
          #                                    rate=flow.rate,
          #                                    deadline=flow.deadline,
          #                                    path=shortest_paths[0])
          #  self._dnc.reserve_resources(reservation, reroute_network, self._first_queue)

          #  # Get a List of Flows sorted by most common edges for first kSP
          #  all_flow_paths = {}
          #  for flow_id, flow_e in self._all_flows.items():
          #      all_flow_paths[flow_id] = flow_e.path

          #  sorted_flows = self._routing.sorted_flow_list_by_edges(all_flow_paths, shortest_paths[0])

          #  rerouted_flows = []
          #  for i in range(min(len(sorted_flows), self._reroutes)):
          #      logger.info(f'Trying Reroute {i} with Flow {sorted_flows[i]}.')
          #      reroute_result = self.reroute_embedded_flow(sorted_flows[i], reroute_networks)

          #      if reroute_result is not None:
          #          result_net, rerouted_flow = reroute_result
          #          reroute_networks = result_net
          #          # Found a working reroute. We can return the network and flow
          #          logger.info(f'Found a working reroute for Flow {sorted_flows[i]}')
          #          flow_emb = EmbeddedFlow(self._last_flow_id, flow, reservation, shortest_path[0], 0)
          #          self._all_flows[self._last_flow_id] = flow_emb
          #          self._last_flow_id += 1
          #          logger.info(f'Flow {flow_emb.id} is now embedded.')
          #          self._flow_reroutes += 1
          #          return flow_emb, reroute_networks, 

           # # Reroute on First Flow SP did not work. We can try on the next SP  
           # if self._reroute_strat == RerouteStrategy.INITFLOW_NSP_QCHANGES or self._reroute_strat == RerouteStrategy.INITFLOW_QCHANGE_NEXTFLOW:
           #     if len(shortest_path) < 2:
           #         return None, network
           #     reroute_networks = copy.deepcopy(network)
           #     reservation = ResourceReservation(burst=flow.burst,
           #                                       rate=flow.rate,
           #                                       deadline=flow.deadline,
           #                                       path=shortest_path[1])
           #     self._dnc.reserve_resources(reservation, reroute_networks, self._first_queue)

           #     # Get a List of Flows sorted by most common edges for first kSP
           #     all_flow_paths = {}
           #     for flow_id, flow_e in self._all_flows.items():
           #         all_flow_paths[flow_id] = flow_e.path

           #     sorted_flows = self._routing.sorted_flow_list_by_edges(all_flow_paths, shortest_path[1])
           #     for i in range(min(len(sorted_flows), self._reroutes)):
           #         logger.info(f'Trying Reroute {i} with Flow {sorted_flows[i]}.')
           #         result_net = self.reroute_embedded_flow(sorted_flows[i], reroute_networks)

           #         if result_net is not None:
           #             reroute_networks = result_net
           #             # Found a working reroute. We can return the network and flow
           #             logger.info(f'Found a working reroute for Flow {sorted_flows[i]}')
           #             flow_emb = EmbeddedFlow(self._last_flow_id, flow, reservation, shortest_path[0], 0)
           #             self._all_flows[self._last_flow_id] = flow_emb
           #             self._last_flow_id += 1
           #             logger.info(f'Flow {flow_emb.id} is now embedded.')
           #             return flow_emb, reroute_networks


            return None, clean_network, None

    def reroute_embedded_flow(self, flow_to_reroute: int, networks: List[Network]) -> Tuple[bool, List[Network]]:
        """
        The Rerouting tries to first move the flow a priority down. If unsuccessful it tries another simple shortest
        path and all

        :param flow_to_reroute: Which Flow ID
        :param networks: List of Networks to keep track of resources
        :return:
        """
        working_network = copy.deepcopy(networks) 
        flow_path = self._all_flows[flow_to_reroute].path
        flow_prio = self._all_flows[flow_to_reroute].priority

        # Remove the reservation from the reroute candidate
        self._dnc.remove_resources(self._all_flows[flow_to_reroute].flow_reservation,
                                   working_network,
                                   self._all_flows[flow_to_reroute].priority)
        
        if self._strategy == LCDNStrategy.GREEDY:
            # The flow we are trying to reroute is removed from the network. try to embed in a lower prioriy 
            for new_prio in range(flow_prio + 1, 4):
                result, working_network = self.embed_flow_on_path(self._all_flows[flow_to_reroute].flow_request, 
                                                                  flow_path, new_prio, working_network, True)
                
                # Violation means either current reroute does not work or new flow wont fit.
                if type(result) is Violation:
                    logger.error(f'Rerouting did not work on Flow {flow_to_reroute} to prio {new_prio}')
                else:
                    # Reroute was successful; Both flows are embedded now.
                    logger.info(f'Rerouting worked for flow {flow_to_reroute} to Q {new_prio}')
                    self._all_flows[flow_to_reroute].priority = new_prio
                    return True, working_network
        
        elif self._strategy == LCDNStrategy.NOTGREEDY:
            # Select the next shortest path:
            flow_src = self._all_flows[flow_to_reroute].flow_request.sourceVM
            flow_dst = self._all_flows[flow_to_reroute].flow_request.destinationVM
            shortest_paths = self._routing.get_shortest_path(flow_src, flow_dst)
            sp = None
            for path in shortest_paths:
                if path != flow_path:
                    sp = path
                    break

            if sp == None: # No alternative was found
                logger.debug(f'No other SP found for {flow_to_reroute}')
                return False, networks
            
            # Try the lowest Queue first
            queues = [i for i in range(len(networks))]
            queues.reverse()
            
            for q in queues:
                result, working_network = self.embed_flow_on_path(self._all_flows[flow_to_reroute].flow_request, 
                                                                  sp, q, working_network, True)
                if type(result) is Violation:
                    logger.error(f'Rerouting did not work on Flow {flow_to_reroute} to prio {q}, path {sp}')
                else:
                    # Reroute was successful; Both flows are embedded now.
                    logger.info(f'Rerouting worked for flow {flow_to_reroute} to Q {q}, path {sp}')
                    self._all_flows[flow_to_reroute].priority = q
                    self._all_flows[flow_to_reroute].path = sp  
                    return True, working_network
                

        return False, networks

    def embed_flow_on_path(self, flow: FlowRequest, path: List[Tuple[int, int]], q_level: int, networks: List[Network], reroute: bool = False) -> Tuple[Union[Violation, EmbeddedFlow], List[Network]]:
        current_networks = copy.deepcopy(networks)

        # Create Reservation
        reservation = ResourceReservation(burst=flow.burst,
                                          rate=flow.rate,
                                          deadline=flow.deadline,
                                          path=path)

        # Reserve the Resource (burst increase etc...), check if flw fits thresholds...
        violation = self._dnc.reserve_resources(reservation, current_networks, q_level)
        if violation:
            # Flow could not fit in the best path. Based on Deadline
            return violation, networks

        # Check whole Network
        violation = self._dnc.check_and_update_network_state(current_networks)

        if violation:
            return violation, networks

        # No Violation occurred. Flow is embedded
        new_flow = EmbeddedFlow(id=self._last_flow_id,
                                flow_request=flow,
                                flow_reservation=reservation,
                                path=path,
                                priority=q_level)

        if not reroute:
            self._all_flows[new_flow.id] = new_flow
            self._last_flow_id += 1

        return new_flow, current_networks

    def remove_flow(self, flow_id: int, networks: List[Network]) -> List[Network]:
        new_network = copy.deepcopy(networks)
        if not flow_id in self._all_flows.keys():
            logger.error(f'Flow with ID {flow_id} does not exist!')
            return False, networks

        flow = self._all_flows.pop(flow_id)
        self._dnc.remove_resources(flow.flow_reservation, new_network, flow.priority)

        return True, new_network

