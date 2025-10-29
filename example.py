from Network.network_components import Node, Edge, Host
from Routing.routing import FlowRequest
from manager import LCDN

if __name__ == '__main__':
    # Create 3 Switches
    n1 = Node(name='node1', node_id=1)
    n2 = Node(name='node2', node_id=2)
    n3 = Node(name='node3', node_id=3)

    # Connect each switch. Makes a full mesh
    l1 = Edge(first_node=1, second_node=2, link_id=1, rate=1e9 / 8, prop_delay=.0, q_size=970000)
    l2 = Edge(first_node=2, second_node=3, link_id=2, rate=1e9 / 8, prop_delay=0.0, q_size=970000)
    l3 = Edge(first_node=1, second_node=3, link_id=3, rate=1e9 / 8, prop_delay=.0, q_size=970000)

    # Add to Host into the network
    h1 = Host(host_id=4,
              host_name='host1',
              mac_address='00:00:00:00:00:01',
              ip_address='10.0.0.1',
              connected_switch=1,
              host_buffer=970000,
              switch_buffer=970000,
              prop_delay=0.0,
              rate=1e9 / 8)

    h2 = Host(host_id=5,
              host_name='host2',
              mac_address='00:00:00:00:00:02',
              ip_address='10.0.0.2',
              connected_switch=2,
              host_buffer=970000,
              switch_buffer=970000,
              prop_delay=0.0,
              rate=1e9 / 8)

    # Add everthing to LCDN
    lcdn = LCDN()
    lcdn.add_node(n1)
    lcdn.add_node(n2)
    lcdn.add_node(n3)
    lcdn.add_edge(l1)
    lcdn.add_edge(l2)
    lcdn.add_edge(l3)
    lcdn.add_host(h1)
    lcdn.add_host(h2)

    # Create the flow request
    f1 = FlowRequest(sourceVM=4, destinationVM=5, protocol=50, burst=70, rate=25e6, deadline=150.0/1e3)
    f2 = FlowRequest(sourceVM=4, destinationVM=5, protocol=70, burst=80, rate=25e6, deadline=50.0/1e3)
    f3 = FlowRequest(sourceVM=4, destinationVM=5, protocol=71, burst=60, rate=100000, deadline=1.8/1e3)

    # Try to embed Flow Request
    path_solution_f1 = lcdn.embed_flow(f1)
    print(path_solution_f1)

    path_solution_f2 = lcdn.embed_flow(f2)
    print(path_solution_f2)

    path_solution_f3 = lcdn.embed_flow(f3)
    print(path_solution_f3)

    lcdn.draw_q_delay()
    lcdn.draw_rate()
    lcdn.draw_burst()