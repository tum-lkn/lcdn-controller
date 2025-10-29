from typing import Union, Tuple

from core.interfaces.i_dnc_agent import IDNCAgent
from core.models.flows import ResourceReservation
from core.models.topology import LCDNTopology
from core.models.violation import Violation
from arrival_curve import  ArrivalCurve
from service_curve import ServiceCurve


class DNCAgent(IDNCAgent):

    def reserve_resources(self, reservation: ResourceReservation, network: LCDNTopology) \
            -> Tuple[Union[Violation, None], LCDNTopology]:

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
            violation = Violation('Flow Deadline', (0, 0), reservation.deadline, new_flow_delay)
            logger.error(f'{violation}')
            return violation

        nx.set_edge_attributes(networks[q_level].get_network_graph(), all_acs, 'arrival_curve')
        if q_level != 0:
            nx.set_edge_attributes(networks[0].get_network_graph(), acs_host, 'arrival_curve')

        return None


    def remove_resources(self, reservation: ResourceReservation, LCDNTopology) -> LCDNTopology:
        pass

    def apply_reservations(self, networks: LCDNTopology) -> LCDNTopology:
        pass