# standard imports
import os

# external imports
from crypto_dev_signer.keystore.dict import DictKeystore
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer
from crypto_dev_signer.eth.transaction import EIP155Transaction
from hexathon import (
        add_0x,
        strip_0x,
        )

# local imports
from chainlib.chain import ChainSpec
from chainlib.eth.tx import (
        unpack,
        Tx,
        )

# eth transactions need an explicit chain parameter as part of their signature
chain_spec = ChainSpec.from_chain_str('evm:ethereum:1')
chain_id = chain_spec.chain_id()

# create keystore and signer
keystore = DictKeystore()
signer = EIP155Signer(keystore)
sender_address = keystore.new()
recipient_address = keystore.new()


# set up a transaction dict source
tx_src = {
    'from': sender_address,
    'to': recipient_address,
    'gas': 21000,
    'gasPrice': 1000000000,
    'value': 1024,
    'data': '0xdeadbeef',
        }
sender_nonce = 0
tx = EIP155Transaction(tx_src, sender_nonce, chain_id)
signature = signer.sign_transaction(tx)
print('signature: {}'.format(signature.hex()))

tx.apply_signature(chain_id, signature)
print('tx with signature: {}'.format(tx.serialize()))

tx_signed_raw_bytes = tx.rlp_serialize()
tx_src = unpack(tx_signed_raw_bytes, chain_spec)
tx_parsed = Tx(tx_src)
print('parsed signed tx: {}'.format(tx_parsed.to_human()))
