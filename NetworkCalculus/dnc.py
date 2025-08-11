import networkx as nx
import logging
import math
from typing import Dict, Tuple, Union, List
from dataclasses import dataclass

from Network.network_components import Network
from NetworkCalculus.arrival_curve import ArrivalCurve
from NetworkCalculus.service_curve import ServiceCurve

logger = logging.getLogger(__name__)


@dataclass
class ResourceReservation:
    path: List[Tuple[int, int]]
    rate: float
    burst: float
    deadline: float

@dataclass
class Violation:
    type: str
    edge: Tuple[int, int]
    max_allowed: float
    current: float

    def __str__(self):
        return f'{self.type} violation occurred on {self.edge}; Value: {self.current:.6f}, Max: {self.max_allowed:.6f}'

class DNCAgent(object):
    def __init__(self):
        super(DNCAgent, self).__init__()

    @staticmethod
    def reserve_resources(reservation: ResourceReservation, networks: List[Network], q_level: int) ->  Union[Violation, None]:
        ac_new = ArrivalCurve(rate=reservation.rate, burst=reservation.burst)

        all_acs = nx.get_edge_attributes(networks[q_level].get_network_graph(), 'arrival_curve')
        all_scs = nx.get_edge_attributes(networks[q_level].get_network_graph(), 'service_curve')

        if q_level != 0:
            acs_host = nx.get_edge_attributes(networks[0].get_network_graph(), 'arrival_curve')
            scs_host = nx.get_edge_attributes(networks[0].get_network_graph(), 'service_curve')
            host_threshold = networks[0].get_threshold()

        q_threshold = networks[q_level].get_threshold()

        new_flow_delay = 0.0

        for i, edge in enumerate(reservation.path):
            if q_level != 0 and i == 0:
                # We are on a host that has a single Q.
                acs_host[edge] = acs_host[edge] + ac_new
                ac_new = scs_host[edge].conv_chameleon(ac_new, host_threshold)
            else:
                all_acs[edge] = all_acs[edge] + ac_new
                ac_new = all_scs[edge].conv_chameleon(ac_new, q_threshold)

            if ac_new.rate == math.inf and ac_new.burst == math.inf:
                violation = Violation('Rate', edge, all_scs[edge].rate, ac_new.rate)
                logger.error(f'{violation}')
                return violation

            if q_level != 0 and i == 0:
                new_flow_delay += host_threshold
            else:
                new_flow_delay += q_threshold

        if new_flow_delay > reservation.deadline:
            violation = Violation('Flow Deadline', (0 , 0), reservation.deadline, new_flow_delay)
            logger.error(f'{violation}')
            return violation

        nx.set_edge_attributes(networks[q_level].get_network_graph(), all_acs, 'arrival_curve')
        if q_level != 0:
            nx.set_edge_attributes(networks[0].get_network_graph(), acs_host, 'arrival_curve')

        return None

    def remove_resources(self, reservation: ResourceReservation, networks: List[Network], q_level: int) -> None:
        ac_to_remove = ArrivalCurve(rate=reservation.rate, burst=reservation.burst)

        all_acs = nx.get_edge_attributes(networks[q_level].get_network_graph(), 'arrival_curve')
        all_scs = nx.get_edge_attributes(networks[q_level].get_network_graph(), 'service_curve')
        q_threshold = networks[q_level].get_threshold()


        for edge in reservation.path:
            all_acs[edge] = all_acs[edge] - ac_to_remove
            ac_to_remove = all_scs[edge].conv_chameleon(ac_to_remove, q_threshold)


        nx.set_edge_attributes(networks[q_level].get_network_graph(), all_acs, 'arrival_curve')

        # Apply to networks
        self.check_and_update_network_state(networks)

        return None


    def check_and_update_network_state(self, networks: List[Network]) -> Union[Violation, None]:
        # Potentially there is a new AC that is not applied to Delays Buffers, and Service Curves
        residuals = None

        for network in networks:
            if residuals:
                self.apply_residual(residuals, network)

            residuals = self.update_network_state(network)

        violation = self.check_all_networks_for_violation(networks)

        return violation

    def check_all_networks_for_violation(self, networks: List[Network]) -> Union[Violation, None]:
        for i in range(len(networks)):
            violation = self.check_for_violations(networks[i])

            if violation:
                return violation

        return None

    @staticmethod
    def check_for_violations(network: Network) -> Union[Violation, None]:
        acs = nx.get_edge_attributes(network.get_network_graph(), 'arrival_curve')
        scs = nx.get_edge_attributes(network.get_network_graph(), 'service_curve')
        buffers = nx.get_edge_attributes(network.get_network_graph(), 'buffer')
        thresholds = nx.get_edge_attributes(network.get_network_graph(), 'threshold')

        for edge in network.get_network_graph().edges():
            ac = acs[edge]
            sc = scs[edge]
            buffer = buffers[edge]
            threshold = thresholds[edge]

            if ac.rate > sc.rate:
                violation = Violation('Rate', edge, sc.rate, ac.rate)
                logger.error(f'{violation} on network prio {network.get_priority()}')
                return violation

            delay = sc.delay(ac)
            buffer_used = sc.buffer_chameleon(ac, network.get_threshold())

            if delay > threshold:
                violation = Violation('Delay', edge, threshold, delay)
                logger.error(f'{violation} on network prio {network.get_priority()}')
                return violation

            if buffer_used > buffer:
                violation = Violation('Buffer', edge, buffer, buffer_used)
                logger.error(f'{violation} on network prio {network.get_priority()}')
                return violation

        return None

    @staticmethod
    def update_network_state(network: Network) -> Dict[Tuple[int, int], ServiceCurve]:
        acs = nx.get_edge_attributes(network.get_network_graph(), 'arrival_curve')
        scs = nx.get_edge_attributes(network.get_network_graph(), 'service_curve')
        costs = nx.get_edge_attributes(network.get_network_graph(), 'cost')
        delays = nx.get_edge_attributes(network.get_network_graph(), 'q_delay')
        residuals = {}

        for edge in network.get_network_graph().edges():
            delay = scs[edge].delay(acs[edge])
            delays[edge] = delay
            residuals[edge] = scs[edge].residual(acs[edge])
            costs[edge] = 1 + 1e6 * delay

        nx.set_edge_attributes(network.get_network_graph(), costs, 'cost')
        nx.set_edge_attributes(network.get_network_graph(), delays, 'q_delay')

        return residuals

    @staticmethod
    def apply_residual(residuals: Dict[Tuple[int, int], ServiceCurve], network_to_apply: Network):
        scs = nx.get_edge_attributes(network_to_apply.get_network_graph(), 'service_curve')
        node_types = nx.get_node_attributes(network_to_apply.get_network_graph(), 'type')

        for edge in network_to_apply.get_network_graph().edges():
            if node_types[edge[0]] == 'host':
                # This is the egress Q of an Host it should not be considered, since it actually only has one.
                continue
            scs[edge] = residuals[edge]

        nx.set_edge_attributes(network_to_apply.get_network_graph(), scs, 'service_curve')

        return network_to_apply
