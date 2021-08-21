# standard imports
import unittest

# local imports
from chainlib.eth.jsonrpc import to_blockheight_param


class TestBlock(unittest.TestCase):

    def test_blockheight_param(self):
        self.assertEqual(to_blockheight_param('latest'), 'latest')
        self.assertEqual(to_blockheight_param(0), 'latest')
        self.assertEqual(to_blockheight_param('pending'), 'pending')
        self.assertEqual(to_blockheight_param(-1), 'pending')
        self.assertEqual(to_blockheight_param(1), '0x0000000000000001')


if __name__ == '__main__':
    unittest.main()
