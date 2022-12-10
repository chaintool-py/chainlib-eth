# standard imports
import unittest

# local imports
from chainlib.eth.contract import (
        ABIContractEncoder,
        ABIContractType,
        )


class TestContract(unittest.TestCase):

    def test_abi_param(self):
        e = ABIContractEncoder()
        e.uint256(42)
        e.bytes32('0x666f6f')
        e.address('0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef')
        e.method('foo')
        e.typ(ABIContractType.UINT256)
        e.typ(ABIContractType.BYTES32)
        e.typ(ABIContractType.ADDRESS)

        self.assertEqual(e.types[0], ABIContractType.UINT256)
        self.assertEqual(e.types[1], ABIContractType.BYTES32)
        self.assertEqual(e.types[2], ABIContractType.ADDRESS)
        self.assertEqual(e.contents[0], '000000000000000000000000000000000000000000000000000000000000002a')
        self.assertEqual(e.contents[1], '0000000000000000000000000000000000000000000000000000000000666f6f')
        self.assertEqual(e.contents[2], '000000000000000000000000deadbeefdeadbeefdeadbeefdeadbeefdeadbeef')

        self.assertEqual(e.get(), 'a08f54bb000000000000000000000000000000000000000000000000000000000000002a0000000000000000000000000000000000000000000000000000000000666f6f000000000000000000000000deadbeefdeadbeefdeadbeefdeadbeefdeadbeef')


    def test_abi_uintn(self):
        e = ABIContractEncoder()
        e.uintn(42, 16)
        e.uintn(13, 32)
        e.uintn(666, 64)
        e.uintn(1337, 128)
        e.method('foo')
        e.typ(ABIContractType.UINT16)
        e.typ(ABIContractType.UINT32)
        e.typ(ABIContractType.UINT64)
        e.typ(ABIContractType.UINT128)

        self.assertEqual(e.contents[0], '000000000000000000000000000000000000000000000000000000000000002a')
        self.assertEqual(e.contents[1], '000000000000000000000000000000000000000000000000000000000000000d')
        self.assertEqual(e.contents[2], '000000000000000000000000000000000000000000000000000000000000029a')
        self.assertEqual(e.contents[3], '0000000000000000000000000000000000000000000000000000000000000539')

        self.assertEqual(e.get(), '5e260038000000000000000000000000000000000000000000000000000000000000002a000000000000000000000000000000000000000000000000000000000000000d000000000000000000000000000000000000000000000000000000000000029a0000000000000000000000000000000000000000000000000000000000000539')


if __name__ == '__main__':
    unittest.main()
