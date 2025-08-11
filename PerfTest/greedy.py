import json
import time
import os
from pathlib import Path
from dataclasses import dataclass
import multiprocessing as mp    
import traceback

from manager import LCDN
from routing_test.topology_converter import LCDNTestTopology
from routing_test.flow_request import LCDNTestFlowRequest
from routing_test.test_parameter import LCDN_PATH, TestParameters
from Routing.routing import RerouteStrategy, LCDNStrategy
from measure_utils import Settings

SEEDS = 12641


def run_single_test(parameters: Settings):
    result = []
    start_time = time.time()

    lcdn = LCDN(logfile=f'LCDN_{parameters.topology_path.name}_{parameters.hosts_per_node}_{parameters.run}.log')
    lcdn.set_reroutings(parameters.reroutings)
    lcdn.set_rerouting_strategy(parameters.reroute_strategy)
    lcdn.set_lcdn_strategy(parameters.strategy)
    lcdn.set_greedy_probability(parameters.greedy_p)

    topology = LCDNTestTopology(parameters.topology_path, parameters.hosts_per_node)
    flow_request_generator = LCDNTestFlowRequest(1e6, 800, 0.02, topology.get_hosts(), parameters.seed)

    for node in topology.get_nodes():
        lcdn.add_node(node)

    for edge in topology.get_edges():
        lcdn.add_edge(edge)

    for host in topology.get_hosts():
        lcdn.add_host(host)

    current_fails = 0
    current_flow_id = 0

    while parameters.max_fails - current_fails > 0:
        flow_request = flow_request_generator.next_flow_request()

        try:
            start_ns = time.time_ns()
            flow_admission = lcdn.embed_flow(flow_request)
            stop_ns = time.time_ns()
        except Exception:
            print(f'Error with these parameters: {parameters}')
            print(traceback.format_exc())
            return parameters, [], lcdn

        if flow_admission is None:
            current_fails += 1
        else:
            result.append(flow_admission)
            current_flow_id += 1

    stop_time = time.time()
    print(f'{parameters.topology_path.name} {parameters.run} took {stop_time - start_time}.')
    result = lcdn.get_all_flows_with_information()
    return parameters, result, lcdn

if __name__ == '__main__':
    path = Path('/home/philip/pd-fastdata/LCDN/Topologies/TZ_small/Layer42.graphml')
    paras = Settings(10, SEEDS, path, 0, 4, 50, LCDNStrategy.GREEDYMIX, 0.5, RerouteStrategy.COMPOUND_FLOWS)
    _, result, lcdn = run_single_test(paras)
    
    delays = lcdn.get_all_q_delays()
    buffers = lcdn.get_all_buffers()
    rates = lcdn.get_all_rates()
    print(lcdn._flow_manager._flow_reroutes)
    print(len(result))
    with open('test_result.json', 'w') as rf:
        json.dump(result, rf)
    print(len(result))

    for i in range(4):
        print(f"Queue {i}")
        for edge in delays[0].keys():
            try:
                print(f"Link {edge}: {delays[i][edge] * 1e3:.5f} | {buffers[i][edge]} | {rates[i][edge]/1e6}")
            except KeyError:
                continue





