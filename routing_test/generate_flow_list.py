import json
from topology_converter import LCDNTestTopology
from flow_request import LCDNTestFlowRequest
from pathlib import Path


def get_topology_list():
    topo_dir = Path('/home/philipd/pd-fastdata/LCDN/Topologies/TZ_small/')
    all_topos = []
    for topology in topo_dir.iterdir():
        all_topos.append(topology)

    return all_topos


def create_flow_request(topo, hpn, seed):
    test_topo = LCDNTestTopology(topo, hpn)
    flow_gen = LCDNTestFlowRequest(1e6, 800, 0.02, test_topo.get_hosts(), seed)

    all_flow_request = []

    for i in range(20000):
        fr = flow_gen.next_flow_request()
        all_flow_request.append({'src': fr.sourceVM, 'dst': fr.destinationVM})

    result = {}
    result['flow'] = {'burst': 800, 'rate': 1e6, 'deadline': 0.02}
    result['hosts_map'] = [{host.host_id: host.connected_switch} for host in test_topo.get_hosts()]
    result['requests'] = all_flow_request
    return result


if __name__ == '__main__':
    for topo in get_topology_list():
        for hpn in [1, 2, 3, 4]:
            for i, seed in enumerate([12641, 4651465, 148971, 90103, 50798]):
                fr = create_flow_request(topo, hpn, seed)

                with open(f'FlowRequests/fr_{topo.name}_hpn{hpn}_run{i}.json', 'w') as file:
                    json.dump(fr, file)

