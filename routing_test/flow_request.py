from routing_test.topology_converter import LCDNTestTopology
from Network.network_components import Host
from Routing.routing import FlowRequest
from typing import List
import numpy as np
from pathlib import Path

class LCDNTestFlowRequest(object):
    def __init__(self, rate: float, burst: int, deadline: float, hosts: List[Host], seed: int):
        self._rate = rate
        self._burst = burst
        self._deadline = deadline
        self._last_proto = 0
        self._hosts = hosts
        self._all_flows = []
        np.random.seed(seed)

    def next_flow_request(self):
        src = np.random.choice(self._hosts).host_id
        dst = np.random.choice(self._hosts).host_id

        while dst == src:
            dst = np.random.choice(self._hosts).host_id

        self._last_proto += 1
        return FlowRequest(src, dst, self._last_proto, self._burst, self._rate, self._deadline)


if __name__ == '__main__':
    host_list = []
    for i in range(12):
        host = Host(i, f'Host {i}', '00.00.00.{i}', '10.0.0.{i}', i % 4, 1e5, 125e3, 7.65 / 1e6, 1e9)
        host_list.append(host)

    flow_gen = LCDNTestFlowRequest(1e6, 800, 0.02, host_list, 12641)
    for i in range(100):
        fr = flow_gen.next_flow_request()
        print(f'{fr.sourceVM}\t - {fr.destinationVM}')
