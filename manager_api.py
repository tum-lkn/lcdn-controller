from fastapi import FastAPI
from manager import LCDN
from pydantic import BaseModel
from manager import FlowRequest
import uvicorn
import logging

logger = logging.getLogger(__name__)

app = FastAPI()
lcdn = LCDN()

last_prot = 0  # Qucik Fix for Flw embed interface

class ClientFlowRequest(BaseModel):
    src_node: int
    dst_ip: str
    rate: float
    burst: float
    deadline: float


def _get_node_id_from_ip(ip: str):
    return lcdn.get_node_id_from_ip(ip)

@app.get('/request-node-id')
def request_node_id(ip: str):
    # Ask LCDN for the ID
    logger.info('New Node ID request for')
    return _get_node_id_from_ip(ip)

@app.get('/try-flow-register')
def try_flow_register(flow_request: ClientFlowRequest):
    # Ask LCDN for the flow path
    logger.info(f'Try Flow Register request from {flow_request.src_node}')
    logger.debug(f'FR: {flow_request.src_node} -> {flow_request.dst_ip}; {flow_request.rate} bits/s, {flow_request.burst} bit, max {flow_request.deadline} s')
    
    # Ask LCDN to embed the current Flow. LCDN returns the VLAN TAG for the spanning tree that contains the route
    path, prio = lcdn.embed_flow(FlowRequest(flow_request.src_node, _get_node_id_from_ip(flow_request.dst_ip), 
                                             last_prot, flow_request.burst, flow_request.rate, flow_request.deadline))

    return 


@app.get('/remove-flow')
def remove_flow():
    # Remove the flow in LCDN
    return {'result': True}


if __name__ == '__main__':
    uvicorn.run(app, host='0.0.0.0', port=8123)
