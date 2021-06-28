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
from chainlib.eth.contract import (
        ABIContractEncoder,
        ABIContractDecoder,
        ABIContractType,
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

# encode the contract parameters
enc = ABIContractEncoder()
enc.method('fooBar')
enc.typ(ABIContractType.ADDRESS)
enc.typ(ABIContractType.UINT256)
enc.address(recipient_address)
enc.uint256(42)
data = enc.get()

# create a new transaction, but output in raw rlp format 
tx_factory = TxFactory(chain_spec, signer=signer, nonce_oracle=nonce_oracle, gas_oracle=gas_oracle)
tx = tx_factory.template(sender_address, recipient_address, use_nonce=True)
tx = tx_factory.set_code(tx, data)
(tx_hash, tx_signed_raw) = tx_factory.finalize(tx, tx_format=TxFormat.RLP_SIGNED)

print('contract transaction: {}'.format(tx))

# retrieve the input data from the transaction
tx_src = unpack(bytes.fromhex(strip_0x(tx_signed_raw)), chain_spec)
data_recovered = strip_0x(tx_src['data'])

# decode the contract parameters 
dec = ABIContractDecoder()
dec.typ(ABIContractType.ADDRESS)
dec.typ(ABIContractType.UINT256)
# (yes, this interface needs to be vastly improved, it should take the whole buffer and advance with cursor itself)
cursor = 8 # the method signature is 8 characters long. input data to the solidity function starts after that
dec.val(data_recovered[cursor:cursor+64])
cursor += 64
dec.val(data_recovered[cursor:cursor+64])
r = dec.decode()

print('contract param 1 {}'.format(r[0]))
print('contract param 2 {}'.format(r[1]))
