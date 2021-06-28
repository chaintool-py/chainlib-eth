# standard imports
import os
import unittest
import logging

# local imports
from chainlib.eth.unittest.ethtester import EthTesterCase
from chainlib.eth.nonce import RPCNonceOracle
from chainlib.eth.gas import (
        RPCGasOracle,
        Gas,
        )
from chainlib.eth.tx import (
        unpack,
        pack,
        raw,
        transaction,
        TxFormat,
        TxFactory,
        Tx,
        )
from chainlib.eth.contract import (
        ABIContractEncoder,
        ABIContractType,
        )
from chainlib.eth.address import to_checksum_address
from hexathon import (
        strip_0x,
        add_0x,
        )

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


class TxTestCase(EthTesterCase):

    def test_tx_reciprocal(self):
        nonce_oracle = RPCNonceOracle(self.accounts[0], self.rpc)
        gas_oracle = RPCGasOracle(self.rpc)
        c = Gas(signer=self.signer, nonce_oracle=nonce_oracle, gas_oracle=gas_oracle, chain_spec=self.chain_spec)
        (tx_hash_hex, o) = c.create(self.accounts[0], self.accounts[1], 1024, tx_format=TxFormat.RLP_SIGNED)
        tx = unpack(bytes.fromhex(strip_0x(o)), self.chain_spec)
        self.assertEqual(tx['from'], self.accounts[0])
        self.assertEqual(tx['to'], self.accounts[1])


    def test_tx_pack(self):
        nonce_oracle = RPCNonceOracle(self.accounts[0], self.rpc)
        gas_oracle = RPCGasOracle(self.rpc)

        mock_contract = to_checksum_address(add_0x(os.urandom(20).hex()))

        f = TxFactory(self.chain_spec, signer=self.rpc)
        enc = ABIContractEncoder()
        enc.method('fooMethod')
        enc.typ(ABIContractType.UINT256)
        enc.uint256(13)
        data = enc.get()
        tx = f.template(self.accounts[0], mock_contract, use_nonce=True)
        tx = f.set_code(tx, data)
        (tx_hash, tx_signed_raw_hex) = f.finalize(tx, TxFormat.RLP_SIGNED)
        logg.debug('tx result {}'.format(tx))
        o = raw(tx_signed_raw_hex)
        r = self.rpc.do(o)
        o = transaction(tx_hash)
        tx_rpc_src = self.rpc.do(o)
        logg.debug('rpc src {}'.format(tx_rpc_src))

        tx_signed_raw_bytes = bytes.fromhex(strip_0x(tx_signed_raw_hex))
        tx_src = unpack(tx_signed_raw_bytes, self.chain_spec)
        txo = Tx(tx_src)
        tx_signed_raw_bytes_recovered = pack(txo, self.chain_spec)
        logg.debug('o {}'.format(tx_signed_raw_bytes.hex()))
        logg.debug('r {}'.format(tx_signed_raw_bytes_recovered.hex()))
        self.assertEqual(tx_signed_raw_bytes, tx_signed_raw_bytes_recovered)

if __name__ == '__main__':
    unittest.main()
