# standard imports
import os

# external iports
from chainlib.eth.tx import (
        TxFactory,
        TxFormat,
        receipt,
        )
from chainlib.eth.contract import (
        ABIContractEncoder,
        #ABIContractDecoder,
        ABIContractType,
        )
from hexathon import add_0x

script_dir = os.path.realpath(os.path.dirname(__file__))
data_dir = script_dir

class TestContract(TxFactory):

    __abi = None
    __bytecode = None

    @staticmethod
    def gas(code=None):
        return 1000000


    @staticmethod
    def abi():
        if TestContract.__abi == None:
            f = open(os.path.join(data_dir, 'TestContract.json'), 'r')
            TestContract.__abi = json.load(f)
            f.close()
        return TestContract.__abi


    @staticmethod
    def bytecode():
        if TestContract.__bytecode == None:
            f = open(os.path.join(data_dir, 'TestContract.bin'))
            TestContract.__bytecode = f.read()
            f.close()
        return TestContract.__bytecode


    def constructor(self, sender_address, tx_format=TxFormat.JSONRPC, id_generator=None):
        code = TestContract.bytecode()
        tx = self.template(sender_address, None, use_nonce=True)
        tx = self.set_code(tx, code)
        return self.finalize(tx, tx_format, id_generator=id_generator)


    def foo(self, contract_address, sender_address, x, y, tx_format=TxFormat.JSONRPC, id_generator=None):
        enc = ABIContractEncoder()
        enc.method('foo')
        enc.typ(ABIContractType.UINT256)
        enc.typ(ABIContractType.BYTES32)
        enc.uint256(x)
        enc.bytes32(y)
        data = add_0x(enc.get())
        tx = self.template(sender_address, contract_address, use_nonce=True)
        tx = self.set_code(tx, data)
        tx = self.finalize(tx, tx_format, id_generator=id_generator)
        return tx
