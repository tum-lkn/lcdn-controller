import json
import time
import os
from pathlib import Path
from dataclasses import dataclass
import multiprocessing as mp    

from manager import LCDN
from routing_test.topology_converter import LCDNTestTopology
from routing_test.flow_request import LCDNTestFlowRequest
from Routing.routing import LCDNStrategy, RerouteStrategy
from PerfTest.measure_utils import LCDN_PATH_LKN, Settings

SEEDS = [12641, 4651465, 148971, 90103, 50798]

def run_single_test(parameters: Settings):
    result = {}
    start_time = time.time()

    lcdn = LCDN()
    lcdn.set_reroutings(parameters.reroutings)
    lcdn.set_rerouting_strategy(parameters.reroute_strategy)
    lcdn.set_lcdn_strategy(parameters.strategy)
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
            flow_admission = lcdn.embed_flow(flow_request)
        except:
            print(f'Error with these parameters: {parameters}')
            return parameters, []

        if flow_admission is None:
            current_fails += 1
        else:
            result[flow_admission['id']] = flow_admission
            for r_flow in flow_admission['rerouted_flows']:
                result[r_flow['id']]['path'] = r_flow['path']
                result[r_flow['id']]['priority'] = r_flow['priority']
            current_flow_id += 1

    stop_time = time.time()
    print(f'{parameters.topology_path.name} {parameters.run} took {stop_time - start_time}.')

    return parameters, result

def create_all_tasks():
    all_tasks = []

    for topology in Path(f'{LCDN_PATH_LKN}Topologies/TZ_small').iterdir():
        for i in range(5):
            new_paras = Settings(10, SEEDS[i], topology, i, 4, 50, LCDNStrategy.GREEDY, 1.0, RerouteStrategy.COMPOUND_FLOWS)
            all_tasks.append(new_paras)

    return all_tasks

def run_all_tests():
    all_tasks = create_all_tasks()
    
    with mp.Pool() as pool:
        result = pool.map(run_single_test, all_tasks)
   
    # Storage
    result_dict = {}
    
    for (parameter, flow_data) in result:
        if parameter.topology_path.name not in result_dict.keys():
            result_dict[parameter.topology_path.name] = {}

        result_dict[parameter.topology_path.name][parameter.run] = flow_data
        
    with open(f'{LCDN_PATH_LKN}Evaluations/LCDN/Paper/Flow2/rerouting_greedy_compoundflows_hpn4.json', 'w') as file:
        json.dump(result_dict, file)

if __name__ == '__main__':
    run_all_tests()
