# standard imports
import unittest
import logging

# local imports
from chainlib.eth.unittest.ethtester import EthTesterCase
from chainlib.eth.contract import (
        ABIContractLogDecoder,
        ABIContractType,
        )

logging.basicConfig(level=logging.DEBUG)


class TestContractLog(EthTesterCase):

    def test_log(self):
        dec = ABIContractLogDecoder()
        dec.topic('TestEventOne')
        dec.typ(ABIContractType.UINT256)
        dec.typ(ABIContractType.BYTES32)
        s = dec.get_signature()
        n = 42
        topics = [
                s,
                n.to_bytes(32, byteorder='big').hex(),
                ]
        data = [
            (b'\xee' * 32).hex(),
                ]
        dec.apply(topics, data)
        o = dec.decode()
        self.assertEqual(o[0], 42)
        self.assertEqual(o[1], data[0])


if __name__ == '__main__':
    unittest.main()
