# standard imports
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
from chainlib.eth.nonce import OverrideNonceOracle
from chainlib.eth.gas import OverrideGasOracle
from chainlib.eth.tx import (
        TxFactory,
        TxFormat,
        unpack,
        pack,
        raw,
        )

# eth transactions need an explicit chain parameter as part of their signature
chain_spec = ChainSpec.from_chain_str('evm:ethereum:1')

# create keystore and signer
keystore = DictKeystore()
signer = EIP155Signer(keystore)
sender_address = keystore.new()
recipient_address = keystore.new()

# explicitly set nonce and gas parameters on this transaction
nonce_oracle = OverrideNonceOracle(sender_address, 0)
gas_oracle = OverrideGasOracle(price=1000000000, limit=21000)

# create a new transaction
tx_factory = TxFactory(chain_spec, signer=signer, nonce_oracle=nonce_oracle, gas_oracle=gas_oracle)
tx = tx_factory.template(sender_address, recipient_address, use_nonce=True)
tx['value'] = 1024
(tx_hash, tx_rpc) = tx_factory.finalize(tx)

print('transaction hash: ' + tx_hash)
print('jsonrpc payload: ' + str(tx_rpc))

# create a new transaction, but output in raw rlp format 
tx = tx_factory.template(sender_address, recipient_address, use_nonce=True) # will now have increased nonce by 1
tx['value'] = 1024
(tx_hash, tx_signed_raw) = tx_factory.finalize(tx, tx_format=TxFormat.RLP_SIGNED) 
print('transaction hash: ' + tx_hash)
print('raw rlp payload: ' + tx_signed_raw)

# convert tx from raw RLP 
tx_signed_raw_bytes = bytes.fromhex(strip_0x(tx_signed_raw))
tx_src = unpack(tx_signed_raw_bytes, chain_spec)
print('tx parsed from rlp payload: ' + str(tx_src))

# .. and back
tx_signed_raw_bytes_recovered = pack(tx_src, chain_spec)
tx_signed_raw_recovered = add_0x(tx_signed_raw_bytes_recovered.hex())
print('raw rlp payload re-parsed: ' + tx_signed_raw_recovered)

# create a raw send jsonrpc payload from the raw RLP
o = raw(tx_signed_raw_recovered)
print('jsonrpc payload: ' + str(o))
