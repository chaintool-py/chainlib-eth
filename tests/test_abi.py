# standard imports
import unittest
import logging
import os

# local imports
from chainlib.eth.contract import (
        ABIContractEncoder,
        ABIContractType,
        )

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()


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


    def test_abi_bytes(self):
        e = ABIContractEncoder()
        e.bytes('deadbeef')
        e.method('foo')
        e.typ(ABIContractType.BYTES)
        self.assertEqual(e.get(), '30c8d1da00000000000000000000000000000000000000000000000000000000000000200000000000000000000000000000000000000000000000000000000000000004deadbeef00000000000000000000000000000000000000000000000000000000')


    def test_abi_string(self):
        e = ABIContractEncoder()
        e.string('deadbeef')
        e.method('foo')
        e.typ(ABIContractType.STRING)
        self.assertEqual(e.get(), 'f31a6969000000000000000000000000000000000000000000000000000000000000002000000000000000000000000000000000000000000000000000000000000000086465616462656566000000000000000000000000000000000000000000000000')


    def test_abi_tuple(self):
        e = ABIContractEncoder()
        e.typ(ABIContractType.STRING)
        e.typ(ABIContractType.BYTES32)
        e.string('deadbeef')
        e.bytes32('666f6f')

        ee = ABIContractEncoder()
        ee.method('foo')
        ee.typ(e)
        ee.typ(ABIContractType.UINT256)
        ee.tuple(e)
        ee.uint256(42)

        self.assertEqual(ee.get_method(), 'foo((string,bytes32),uint256)')
        r = ee.get()
        self.assertEqual(r[:8], '7bab4ebd')
        r = r[8:]
        valid = [
                '0000000000000000000000000000000000000000000000000000000000000040',
                '000000000000000000000000000000000000000000000000000000000000002a',
                '0000000000000000000000000000000000000000000000000000000000000040',
                '0000000000000000000000000000000000000000000000000000000000666f6f',
                '0000000000000000000000000000000000000000000000000000000000000008',
                '6465616462656566000000000000000000000000000000000000000000000000',
                ]

        i = 0
        c = 0
        while c < len(r):
            v = r[c:c+64]
            logg.debug('check position {} {}'.format((i*32).to_bytes(2, byteorder='big').hex(), v))
            self.assertEqual(v, valid[i])
            c += 64
            i += 1


    def test_abi_tuple_embedded(self):
        a = os.urandom(20)
        ea = ABIContractEncoder()
        ea.typ(ABIContractType.STRING)
        ea.typ(ABIContractType.ADDRESS)
        ea.string('foo@bar.com')
        ea.address(a.hex())

        b = os.urandom(20)
        eb = ABIContractEncoder()
        eb.typ(ABIContractType.STRING)
        eb.typ(ABIContractType.ADDRESS)
        eb.string('baz@xyzzy.org')
        eb.address(b.hex())

        ee = ABIContractEncoder()
        ee.typ(ea)
        ee.typ(eb)
        ee.typ(ABIContractType.STRING)
        ee.tuple(ea)
        ee.tuple(eb)
        ee.string('barbarbar')

        e = ABIContractEncoder()
        e.method('foo')
        e.typ(ee)
        e.typ(ABIContractType.UINT256)
        e.tuple(ee)
        e.uint256(42)

        self.assertEqual(e.get_method(), 'foo(((string,address),(string,address),string),uint256)')
        r = e.get()
        print(r)
        self.assertEqual(r[:8], '8cd9051d')
        r = r[8:]

        valid = [
                '0000000000000000000000000000000000000000000000000000000000000040',
                '000000000000000000000000000000000000000000000000000000000000002a',
                '0000000000000000000000000000000000000000000000000000000000000060',
                '00000000000000000000000000000000000000000000000000000000000000e0',
                '0000000000000000000000000000000000000000000000000000000000000160',
                '0000000000000000000000000000000000000000000000000000000000000040',
                '000000000000000000000000' + a.hex(),
                '000000000000000000000000000000000000000000000000000000000000000b',
                '666f6f406261722e636f6d000000000000000000000000000000000000000000',
                '0000000000000000000000000000000000000000000000000000000000000040',
                '000000000000000000000000' + b.hex(),
                '000000000000000000000000000000000000000000000000000000000000000d',
                '62617a4078797a7a792e6f726700000000000000000000000000000000000000',
                '0000000000000000000000000000000000000000000000000000000000000009',
                '6261726261726261720000000000000000000000000000000000000000000000',
                ]

        i = 0
        c = 0
        while c < len(r):
            v = r[c:c+64]
            logg.debug('check position {} {}'.format((i*32).to_bytes(2, byteorder='big').hex(), v))
            self.assertEqual(v, valid[i])
            c += 64
            i += 1



if __name__ == '__main__':
    unittest.main()
