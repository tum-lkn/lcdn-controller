import json
import time
import os
from pathlib import Path
from dataclasses import dataclass
import multiprocessing as mp    

from manager import LCDN
from topology_converter import LCDNTestTopology
from flow_request import LCDNTestFlowRequest
from test_parameter import LCDN_PATH, TestParameters
from Routing.routing import RerouteStrategy

SEEDS = 12641


def run_single_test(parameters: TestParameters):
    result = []
    start_time = time.time()

    lcdn = LCDN(logfile=f'LCDN_{parameters.topology_path.name}_{parameters.hosts_per_node}_{parameters.q_level}_{parameters.run}.log')
    lcdn.set_initial_sps(parameters.init_ksp)
    lcdn.set_reroutings(parameters.reroutings)
    lcdn.set_ksp_offset(parameters.ksp_offset)
    lcdn.set_initial_q_level(parameters.q_level)

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
            flow_path, flow_prio = lcdn.embed_flow(flow_request)
            stop_ns = time.time_ns()
        except:
            print(f'Error with these parameters: {parameters}')
            return parameters, []

        if flow_path is None:
            current_fails += 1
        else:
            tmp_flow_item = {}
            tmp_flow_item['id'] = current_flow_id
            tmp_flow_item['embed_time'] = stop_ns - start_ns
            tmp_flow_item['path'] = flow_path
            tmp_flow_item['priority'] = flow_prio
            tmp_flow_item['src'] = flow_request.sourceVM
            tmp_flow_item['dst'] = flow_request.destinationVM
            result.append(tmp_flow_item)
            current_flow_id += 1

    stop_time = time.time()
    print(f'{parameters.topology_path.name} {parameters.run} offset {parameters.ksp_offset} hpn {parameters.hosts_per_node} took {stop_time - start_time}.')
    result = lcdn.get_all_flows_with_information()
    return parameters, result, lcdn

if __name__ == '__main__':
    path = Path('/home/philip/pd-fastdata/LCDN/Topologies/TZ_small/Layer42.graphml')
    paras = TestParameters(1, 10, 0, SEEDS, path, 0, 4, 50, 0, RerouteStrategy.QCHANGES)
    _, result, lcdn = run_single_test(paras)
    
    delays = lcdn.get_all_q_delays()
    buffers = lcdn.get_all_buffers()
    rates = lcdn.get_all_rates()
    print(lcdn._flow_manager._flow_reroutes)
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





