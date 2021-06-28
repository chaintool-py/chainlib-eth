# standard imports
import sys
import os

# external imports
from crypto_dev_signer.keystore.dict import DictKeystore
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer
from hexathon import (
        add_0x,
        strip_0x,
        )

# local imports
from chainlib.chain import ChainSpec
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.nonce import RPCNonceOracle
from chainlib.eth.gas import RPCGasOracle
from chainlib.eth.tx import (
        TxFactory,
        TxFormat,
        )
from chainlib.error import JSONRPCException

# eth transactions need an explicit chain parameter as part of their signature
chain_spec = ChainSpec.from_chain_str('evm:ethereum:1')

# create keystore and signer
keystore = DictKeystore()
signer = EIP155Signer(keystore)
sender_address = keystore.new()
recipient_address = keystore.new()

# set up node connection
rpc_provider = os.environ.get('RPC_PROVIDER', 'http://localhost:8545')
rpc = EthHTTPConnection(rpc_provider)

# check the connection
if not rpc.check():
    sys.stderr.write('node {} not usable\n'.format(rpc_provider))
    sys.exit(1)

# nonce will now be retrieved from network
nonce_oracle = RPCNonceOracle(sender_address, rpc)

# gas price retrieved from network, and limit from callback
def calculate_gas(code=None):
    return 21000
gas_oracle = RPCGasOracle(rpc, code_callback=calculate_gas)

# create a new transaction
tx_factory = TxFactory(chain_spec, signer=signer, nonce_oracle=nonce_oracle, gas_oracle=gas_oracle)
tx = tx_factory.template(sender_address, recipient_address, use_nonce=True)
tx['value'] = 1024
(tx_hash, tx_rpc) = tx_factory.finalize(tx)

print('transaction hash: ' + tx_hash)
print('jsonrpc payload: ' + str(tx_rpc))
