from pathlib import Path
from dataclasses import dataclass
from Routing.routing import LCDNStrategy, RerouteStrategy 

LCDN_PATH_LKN = '/home/lkn/FNAS/LCDN/'
LCDN_PATH_LOCAL = '/home/philipd/pd-fastdata/LCDN/'

@dataclass
class Settings:
    reroutings: int
    seed: int
    topology_path: Path
    run: int
    hosts_per_node: int
    max_fails: int
    strategy: LCDNStrategy
    greedy_p: float
    reroute_strategy: RerouteStrategy = RerouteStrategy.SINGLE_FLOW
