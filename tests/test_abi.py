from chainlib.eth.contract import (
        ABIContractEncoder,
        ABIContractType,
        )


def test_abi_param():

    e = ABIContractEncoder()
    e.uint256(42)
    e.bytes32('0x666f6f')
    e.address('0xdeadbeefdeadbeefdeadbeefdeadbeefdeadbeef')
    e.method('foo')
    e.typ(ABIContractType.UINT256)
    e.typ(ABIContractType.BYTES32)
    e.typ(ABIContractType.ADDRESS)

    assert e.types[0] == ABIContractType.UINT256
    assert e.types[1] == ABIContractType.BYTES32
    assert e.types[2] == ABIContractType.ADDRESS
    assert e.contents[0] == '000000000000000000000000000000000000000000000000000000000000002a'
    assert e.contents[1] == '0000000000000000000000000000000000000000000000000000000000666f6f'
    assert e.contents[2] == '000000000000000000000000deadbeefdeadbeefdeadbeefdeadbeefdeadbeef'

    assert e.get() == 'a08f54bb000000000000000000000000000000000000000000000000000000000000002a0000000000000000000000000000000000000000000000000000000000666f6f000000000000000000000000deadbeefdeadbeefdeadbeefdeadbeefdeadbeef'


if __name__ == '__main__':
    test_abi_param()
