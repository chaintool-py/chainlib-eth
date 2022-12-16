# standard imports
import unittest
import os
import datetime
import logging

# local imports
from chainlib.eth.jsonrpc import to_blockheight_param
from chainlib.eth.block import Block
from chainlib.eth.dialect import DialectFilter

logging.basicConfig(level=logging.DEBUG)


class TestBlock(unittest.TestCase):


    def test_block(self):
        tx_one_src = {
            'hash': os.urandom(32).hex(),
            'from': os.urandom(20).hex(),
            'to': os.urandom(20).hex(),
            'value': 13,
            'data': '0xdeadbeef',
            'nonce': 666,
            'gasPrice': 100,
            'gas': 21000,
                }

        tx_two_src_hash = os.urandom(32).hex()

        block_hash = os.urandom(32).hex()
        parent_hash = os.urandom(32).hex()
        block_author = os.urandom(20).hex()
        block_time = datetime.datetime.utcnow().timestamp()
        block_src = {
            'number': 42,
            'hash': block_hash,
            'author': block_author,
            'transactions': [
                tx_one_src,
                tx_two_src_hash,
                ],
            'timestamp': block_time,
            'gas_used': '0x1234',
            'gas_limit': '0x2345',
            'parent_hash': parent_hash 
                }
        block = Block(block_src)

        self.assertEqual(block.number, 42)
        self.assertEqual(block.hash, block_hash)
        self.assertEqual(block.author, block_author)
        self.assertEqual(block.timestamp, int(block_time))

        tx_index = block.tx_index_by_hash(tx_one_src['hash'])
        self.assertEqual(tx_index, 0)

        tx_retrieved = block.tx_by_index(tx_index)
        self.assertEqual(tx_retrieved.hash, tx_one_src['hash'])

        tx_index = block.tx_index_by_hash(tx_two_src_hash)
        self.assertEqual(tx_index, 1)


    def test_blockheight_param(self):
        self.assertEqual(to_blockheight_param('latest'), 'latest')
        self.assertEqual(to_blockheight_param(0), 'latest')
        self.assertEqual(to_blockheight_param('pending'), 'pending')
        self.assertEqual(to_blockheight_param(-1), 'pending')
        self.assertEqual(to_blockheight_param(1), '0x0000000000000001')


if __name__ == '__main__':
    unittest.main()
