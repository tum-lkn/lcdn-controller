import json
import time
import os
from pathlib import Path
from dataclasses import dataclass
import multiprocessing as mp    

from manager import LCDN
from Routing.routing import RerouteStrategy
from topology_converter import LCDNTestTopology
from flow_request import LCDNTestFlowRequest
from test_parameter import LCDN_PATH, TestParameters

SEEDS = [12641, 4651465, 148971, 90103, 50798]

def run_single_test(parameters: TestParameters):
    result = []
    start_time = time.time()

    lcdn = LCDN()
    lcdn.set_initial_sps(parameters.init_ksp)
    lcdn.set_reroutings(parameters.reroutings)
    lcdn.set_ksp_offset(parameters.ksp_offset)
    lcdn.set_initial_q_level(parameters.q_level)
    lcdn.set_rerouting_strategy(parameters.reroute_strat)

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
    return parameters, result

def create_all_tasks():
    all_tasks = []
    reroute_strats = [
        RerouteStrategy.QCHANGES,
#        RerouteStrategy.QCHANGES_NEXTSP,
#        RerouteStrategy.INITFLOW_QCHANGE_NEXTFLOW,
#        RerouteStrategy.INITFLOW_NSP_QCHANGES
    ]

    for strat in reroute_strats:
        for hs_per_node in [ 4]:
            for topology in Path(f'{LCDN_PATH}Topologies/TZ_small').iterdir():
                for i in range(5):
                    new_paras = TestParameters(1, 10, 0, SEEDS[i], topology, i, hs_per_node, 50, 0, strat)
                    all_tasks.append(new_paras)

    return all_tasks

def run_all_tests():
    all_tasks = create_all_tasks()
    
    with mp.Pool() as pool:
        result = pool.map(run_single_test, all_tasks)
   
    # Storage
    result_dict = { 
        "QCHANGES": {},
        "QCHANGES_NEXTSP": {},
        "INITFLOW_QCHANGE_NEXTFLOW": {},
        "INITFLOW_NSP_QCHANGES": {}
    }

    for (parameter, flow_data) in result:
        if f'hpn{parameter.hosts_per_node}' not in result_dict[f'{parameter.reroute_strat.name}'].keys():
            result_dict[f'{parameter.reroute_strat.name}'][f'hpn{parameter.hosts_per_node}'] = {}

        if parameter.topology_path.name not in result_dict[f'{parameter.reroute_strat.name}'][f'hpn{parameter.hosts_per_node}'].keys():
            result_dict[f'{parameter.reroute_strat.name}'][f'hpn{parameter.hosts_per_node}'][parameter.topology_path.name] = {}
        
        result_dict[f'{parameter.reroute_strat.name}'][f'hpn{parameter.hosts_per_node}'][parameter.topology_path.name][parameter.run] = flow_data
        
    with open(f'{LCDN_PATH}Evaluations/LCDN/Paper/Flow2/reroute_strats.json', 'w') as file:
        json.dump(result_dict, file)

if __name__ == '__main__':
    run_all_tests()
