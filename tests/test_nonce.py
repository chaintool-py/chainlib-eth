# standard imports
import os
import unittest

# local imports
from chainlib.eth.address import to_checksum_address
from chainlib.eth.nonce import OverrideNonceOracle
from hexathon import add_0x

# test imports
from tests.base import TestBase


class TestNonce(TestBase):

    def test_nonce(self):
        addr_bytes = os.urandom(20)
        addr = add_0x(to_checksum_address(addr_bytes.hex()))
        n = OverrideNonceOracle(addr, 42)
        self.assertEqual(n.get_nonce(), 42)
        self.assertEqual(n.next_nonce(), 42)
        self.assertEqual(n.next_nonce(), 43)


if __name__ == '__main__':
    unittest.main()
