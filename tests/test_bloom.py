# standard imports
import os
import unittest
import logging

# local imports
from chainlib.eth.unittest.ethtester import EthTesterCase
from chainlib.eth.nonce import RPCNonceOracle
from chainlib.eth.gas import OverrideGasOracle
from chainlib.eth.tx import receipt
from chainlib.eth.block import block_by_number
from chainlib.eth.log import LogBloom
from hexathon import (
        strip_0x,
        add_0x,
        )

# test imports
from tests.contract import TestContract

script_dir = os.path.realpath(os.path.dirname(__file__))

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()

#{'blockHash': '0xe657e31045be85cfff8c28af6b4fd6417cace7150c4ebbeb736e638313d8e66d', 'block_hash': '0xe657e31045be85cfff8c28af6b4fd6417cace7150c4ebbeb736e638313d8e66d', 'blockNumber': '0xc1ee5a', 'block_number': '0xc1ee5a', 'contractAddress': None, 'contract_address': None, 'cumulativeGasUsed': '0xbc659', 'cumulative_gas_used': '0xbc659', 'from': '0xf6025e63cee5e436a5f1486e040aeead7e97b745', 'gasUsed': '0x1dddb', 'gas_used': '0x1dddb', 'logs': [

#{'address': '0x4e58ab12d2051ea2068e78e4fcee7ddee6785848', 'blockHash': '0xe657e31045be85cfff8c28af6b4fd6417cace7150c4ebbeb736e638313d8e66d', 'blockNumber': '0xc1ee5a', 'data': '0x', 'logIndex': '0xd', 'removed': False, 'topics': ['0x92e98423f8adac6e64d0608e519fd1cefb861498385c6dee70d58fc926ddc68c', '0x0000000000000000000000000000000000000000000000000000000005f6aa5a', '0x00000000000000000000000000000000000000000000000000000000000000d6', '0x000000000000000000000000f6025e63cee5e436a5f1486e040aeead7e97b745'], 'transactionHash': '0xd0f039591953d277d55f628694248cb442590fab95ac53fcfb69e9dbba7db97a', 'transactionIndex': '0xe'},

#{'address': '0x4e58ab12d2051ea2068e78e4fcee7ddee6785848', 'blockHash': '0xe657e31045be85cfff8c28af6b4fd6417cace7150c4ebbeb736e638313d8e66d', 'blockNumber': '0xc1ee5a', 'data': '0x0000000000000000000000000000000000000000000000000000000060d7119f', 'logIndex': '0xe', 'removed': False, 'topics': ['0x0559884fd3a460db3073b7fc896cc77986f16e378210ded43186175bf646fc5f', '0x0000000000000000000000000000000000000000000000000000000005f6aa5a', '0x00000000000000000000000000000000000000000000000000000000000000d6'], 'transactionHash': '0xd0f039591953d277d55f628694248cb442590fab95ac53fcfb69e9dbba7db97a', 'transactionIndex': '0xe'},

#{'address': '0x4e58ab12d2051ea2068e78e4fcee7ddee6785848', 'blockHash': '0xe657e31045be85cfff8c28af6b4fd6417cace7150c4ebbeb736e638313d8e66d', 'blockNumber': '0xc1ee5a', 'data': '0x', 'logIndex': '0xf', 'removed': False, 'topics': ['0xfe25c73e3b9089fac37d55c4c7efcba6f04af04cebd2fc4d6d7dbb07e1e5234f', '0x0000000000000000000000000000000000000000000000813b65aa80e5770000'], 'transactionHash': '0xd0f039591953d277d55f628694248cb442590fab95ac53fcfb69e9dbba7db97a', 'transactionIndex': '0xe'}]

#, 'logsBloom': '0x0000000000000000000000000000000000000080000000000000000000c000000000000000408000000000000000000000000000000200080000000000000000100000000000000000000000000000000000000000000200000020000000000000000000000000800000400000000000400000000400000000000400100000000000000000000000000000000000000000000480000000000000000000000000000000000000000000000000008000000000080000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000002008000000000000000', 'logs_bloom': '0x0000000000000000000000000000000000000080000000000000000000c000000000000000408000000000000000000000000000000200080000000000000000100000000000000000000000000000000000000000000200000020000000000000000000000000800000400000000000400000000400000000000400100000000000000000000000000000000000000000000480000000000000000000000000000000000000000000000000008000000000080000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000002008000000000000000', 'status': '0x1', 'to': '0x4e58ab12d2051ea2068e78e4fcee7ddee6785848', 'transactionHash': '0xd0f039591953d277d55f628694248cb442590fab95ac53fcfb69e9dbba7db97a', 'transaction_hash': '0xd0f039591953d277d55f628694248cb442590fab95ac53fcfb69e9dbba7db97a', 'transactionIndex': '0xe', 'transaction_index': '0xe', 'type': '0x0'}


class BloomTestCase(EthTesterCase):

    def setUp(self):
        super(BloomTestCase, self).setUp()

        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.rpc)
        c = TestContract(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        (tx_hash, o) = c.constructor(self.accounts[0])
        r = self.rpc.do(o)
        o = receipt(tx_hash)
        r = self.rpc.do(o)
        self.assertEqual(r['status'], 1)

        self.address = r['contract_address']
        logg.info('deployed contract on {}'.format(self.address))
       

    def test_log_proof(self):
        bloom = LogBloom()

        address = bytes.fromhex(strip_0x('0x4e58ab12d2051ea2068e78e4fcee7ddee6785848'))
        logs = [
            ['0x92e98423f8adac6e64d0608e519fd1cefb861498385c6dee70d58fc926ddc68c', '0x0000000000000000000000000000000000000000000000000000000005f6aa5a', '0x00000000000000000000000000000000000000000000000000000000000000d6', '0x000000000000000000000000f6025e63cee5e436a5f1486e040aeead7e97b745'],
            ['0x0559884fd3a460db3073b7fc896cc77986f16e378210ded43186175bf646fc5f', '0x0000000000000000000000000000000000000000000000000000000005f6aa5a', '0x00000000000000000000000000000000000000000000000000000000000000d6'],
            ['0xfe25c73e3b9089fac37d55c4c7efcba6f04af04cebd2fc4d6d7dbb07e1e5234f', '0x0000000000000000000000000000000000000000000000813b65aa80e5770000'],
                ]
   
        bloom.add(address)
        for topics in logs:
            topics_bytes = []
            for topic in topics:
                topic_bytes = bytes.fromhex(strip_0x(topic))
                bloom.add(topic_bytes)

        log_proof_hex = '0x0000000000000000000000000000000000000080000000000000000000c000000000000000408000000000000000000000000000000200080000000000000000100000000000000000000000000000000000000000000200000020000000000000000000000000800000400000000000400000000400000000000400100000000000000000000000000000000000000000000480000000000000000000000000000000000000000000000000008000000000080000000000000000000000000000000000000000000000000000000008000000000000000000000000000000000000000000000000000000000000000000000000000002008000000000000000'
        log_proof = bytes.fromhex(strip_0x(log_proof_hex))

        log_proof_bitcount = 0
        for b in log_proof:
            for i in range(8):
                if b & (1 << (7 - i)) > 0:
                    log_proof_bitcount += 1
        logg.debug('proof log has {} bits set'.format(log_proof_bitcount))

        log_created_bitcount = 0
        for b in bloom.content:
            for i in range(8):
                if b & (1 << (7 - i)) > 0:
                    log_created_bitcount += 1
        logg.debug('created log has {} bits set'.format(log_created_bitcount))

        logg.debug('log_proof:\n{}'.format(log_proof_hex))
        logg.debug('log_created:\n{}'.format(add_0x(bloom.content.hex())))
        for i in range(len(bloom.content)):
            chk = bloom.content[i] & log_proof[i]
            if chk != bloom.content[i]:
                self.fail('mismatch at {}: {} != {}'.format(i, chk, bloom.content[i]))

        

    @unittest.skip('pyevm tester produces bogus log blooms')
    def test_log(self):
        nonce_oracle = RPCNonceOracle(self.accounts[0], conn=self.rpc)
        gas_oracle = OverrideGasOracle(limit=50000, conn=self.rpc)
        c = TestContract(self.chain_spec, signer=self.signer, nonce_oracle=nonce_oracle)
        b = b'\xee' * 32
        (tx_hash, o) = c.foo(self.address, self.accounts[0], 42, b.hex())
        r = self.rpc.do(o)
        o = receipt(tx_hash)
        rcpt = self.rpc.do(o)
        self.assertEqual(rcpt['status'], 1)

        bloom = LogBloom()
        topic = rcpt['logs'][0]['topics'][0]
        topic = bytes.fromhex(strip_0x(topic))
        address = bytes.fromhex(strip_0x(self.address))
        bloom.add(topic, address)

        o = block_by_number(rcpt['block_number'])
        r = self.rpc.do(o)


if __name__ == '__main__':
    unittest.main()
