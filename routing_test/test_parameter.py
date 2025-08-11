from pathlib import Path
from dataclasses import dataclass
from Routing.routing import RerouteStrategy 

LCDN_PATH = '/home/philipd/pd-fastdata/LCDN/'

@dataclass
class TestParameters:
    init_ksp: int
    reroutings: int
    ksp_offset: int
    seed: int
    topology_path: Path
    run: int
    hosts_per_node: int
    max_fails: int
    q_level: int    
    reroute_strat: RerouteStrategy
