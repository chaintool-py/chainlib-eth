# standard imports
import os

# external imports
from hexathon import strip_0x, add_0x

# local imports
from chainlib.eth.gas import balance, parse_balance
from chainlib.eth.connection import EthHTTPConnection


# create a random address to check
address_bytes = os.urandom(20)
address = add_0x(address_bytes.hex())

# connect to rpc node and send request for balance 
rpc_provider = os.environ.get('RPC_PROVIDER', 'http://localhost:8545')
rpc = EthHTTPConnection(rpc_provider)
o = balance(address)
r = rpc.do(o)

clean_address = strip_0x(address)
clean_balance = parse_balance(r)
    
print('address {} has balance {}'.format(clean_address, clean_balance))
