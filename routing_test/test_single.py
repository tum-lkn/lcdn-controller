from pathlib import Path
from manager import LCDN
from routing_ksp_offset import TestParameters
from flow_request import LCDNTestFlowRequest
from topology_converter import LCDNTestTopology

def run_test(parameter: TestParameters):
    result = []
    lcdn = LCDN()
    lcdn.set_ksp_offset(parameter.ksp_offset)
    lcdn.set_reroutings(parameter.reroutings)
    lcdn.set_initial_sps(3)

    topology = LCDNTestTopology(parameter.topology_path, parameter.hosts_per_node)
    flow_request_generator = LCDNTestFlowRequest(1e6, 800, 0.02, topology.get_hosts(), parameter.seed)

    for node in topology.get_nodes():
        lcdn.add_node(node)

    for edge in topology.get_edges():
        lcdn.add_edge(edge)

    for host in topology.get_hosts():
        lcdn.add_host(host)

    current_fails = 0
    current_flow_id = 0

    while parameter.max_fails - current_fails > 0:
        print(f'Working on Flow {current_flow_id}')
        flow_request = flow_request_generator.next_flow_request()

        flow_result = lcdn.embed_flow(flow_request)


        if flow_request is None:
            current_fails += 1
        else:
            result.append({current_flow_id: 1})
            current_flow_id += 1

        return


if __name__ == '__main__':
    para = TestParameters(3, 0, 3, 12641, Path('/home/philipd/pd-fastdata/LCDN/Topologies/TZ_small/Basnet.graphml'), 0, 4, 50)
    run_test(para)
    
