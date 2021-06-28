# standard imports
import os
import sys

# local imports
from chainlib.jsonrpc import jsonrpc_template
from chainlib.eth.connection import EthHTTPConnection

# set up node connection and execute rpc call
rpc_provider = os.environ.get('RPC_PROVIDER', 'http://localhost:8545')
rpc = EthHTTPConnection(rpc_provider)

# check the connection
if not rpc.check():
    sys.stderr.write('node {} not usable\n'.format(rpc_provider))
    sys.exit(1)

# build and send rpc call
o = jsonrpc_template()
o['method'] = 'eth_blockNumber'
r = rpc.do(o)

# interpret result for humans
try:
    block_number = int(r, 10)
except ValueError:
    block_number = int(r, 16)

print('block number {}'.format(block_number))
