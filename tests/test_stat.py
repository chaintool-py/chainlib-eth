# standard imports
import unittest
import datetime
import os

# external imports
from chainlib.stat import ChainStat
from chainlib.eth.block import Block


class TestStat(unittest.TestCase):

    def test_block(self):

        s = ChainStat()
 
        d = datetime.datetime.utcnow() - datetime.timedelta(seconds=30)
        block_a = Block({
            'timestamp': d.timestamp(),
            'hash': None,
            'transactions': [],
            'number': 41,
            'author': os.urandom(20).hex(),
            'gas_used': '0x1234',
            'gas_limit': '0x2345',
            'parent_hash': None,
            })

        d = datetime.datetime.utcnow()
        block_b = Block({
            'timestamp': d.timestamp(),
            'hash': None,
            'transactions': [],
            'number': 42,
            'author': os.urandom(20).hex(),
            'gas_used': '0x1234',
            'gas_limit': '0x2345',
            'parent_hash': None,
            })

        s.block_apply(block_a)
        s.block_apply(block_b)
        self.assertEqual(s.block_average(), 30.0)

        d = datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
        block_c = Block({
            'timestamp': d.timestamp(),
            'hash': None,
            'transactions': [],
            'number': 43,
            'author': os.urandom(20).hex(),
            'gas_used': '0x1234',
            'gas_limit': '0x2345',
            'parent_hash': None,
            })

        s.block_apply(block_c)
        self.assertEqual(s.block_average(), 20.0)


if __name__ == '__main__':
    unittest.main()
