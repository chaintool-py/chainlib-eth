import unittest

from chainlib.eth.address import (
        is_address,
        is_checksum_address,
        to_checksum,
        )

from tests.base import TestBase


class TestChain(TestBase):

    def test_chain_spec(self):
        checksum_address = 'Eb3907eCad74a0013c259D5874AE7f22DcBcC95C'
        plain_address = checksum_address.lower()

        self.assertEqual(checksum_address, to_checksum(checksum_address))

        self.assertTrue(is_address(plain_address))
        self.assertFalse(is_checksum_address(plain_address))
        self.assertTrue(is_checksum_address(checksum_address))

        self.assertFalse(is_address(plain_address + "00"))
        self.assertFalse(is_address(plain_address[:len(plain_address)-2]))

        with self.assertRaises(ValueError):
            to_checksum(plain_address + "00")

        with self.assertRaises(ValueError):
            to_checksum(plain_address[:len(plain_address)-2])


if __name__ == '__main__':
    unittest.main()
