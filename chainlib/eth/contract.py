# standard imports
import enum
import re
import logging

# external imports
from hexathon import (
        strip_0x,
        pad,
        )

# local imports
from chainlib.hash import keccak256_string_to_hex
from chainlib.block import BlockSpec
from chainlib.jsonrpc import JSONRPCRequest
from .address import to_checksum_address

logg = logging.getLogger(__name__)


re_method = r'^[a-zA-Z0-9_]+$'

class ABIContractType(enum.Enum):
    """Data types used by ABI encoders
    """
    BYTES32 = 'bytes32'
    BYTES4 = 'bytes4'
    UINT256 = 'uint256'
    ADDRESS = 'address'
    STRING = 'string'
    BOOLEAN = 'bool'

dynamic_contract_types = [
    ABIContractType.STRING,
    ]


class ABIContract:
    """Base class for Ethereum smart contract encoder
    """
    def __init__(self):
        self.types = []
        self.contents = []


class ABIMethodEncoder(ABIContract):
    """Generate ABI method signatures from method signature string.
    """
    def __init__(self):
        super(ABIMethodEncoder, self).__init__()
        self.method_name = None
        self.method_contents = []


    def method(self, m):
        """Set method name.

        :param m: Method name
        :type m: str
        :raises ValueError: Invalid method name
        """
        if re.match(re_method, m) == None:
            raise ValueError('Invalid method {}, must match regular expression {}'.format(re_method))
        self.method_name = m
        self.__log_method()


    def get_method(self):
        """Return currently set method signature string.

        :rtype: str
        :returns: Method signature
        """
        if self.method_name == None:
            return ''
        return '{}({})'.format(self.method_name, ','.join(self.method_contents))


    def typ(self, v):
        """Add argument type to argument vector.

        Method name must be set before this is called.

        :param v: Type to add
        :type v: chainlib.eth.contract.ABIContractType
        :raises AttributeError: Type set before method name
        :raises TypeError: Invalid type
        """
        if self.method_name == None:
            raise AttributeError('method name must be set before adding types')
        if not isinstance(v, ABIContractType):
            raise TypeError('method type not valid; expected {}, got {}'.format(type(ABIContractType).__name__, type(v).__name__))
        self.method_contents.append(v.value)
        self.__log_method()


    def __log_method(self):
        logg.debug('method set to {}'.format(self.get_method()))



class ABIContractDecoder(ABIContract):
    """Decode serialized ABI contract input data to corresponding python primitives.
    """
    
    def typ(self, v):
        """Add type to argument array to parse input against.

        :param v: Type
        :type v: chainlib.eth.contract.ABIContractType
        :raises TypeError: Invalid type
        """
        if not isinstance(v, ABIContractType):
            raise TypeError('method type not valid; expected {}, got {}'.format(type(ABIContractType).__name__, type(v).__name__))
        self.types.append(v.value)
        self.__log_typ()


    def val(self, v):
        """Add value to value array.

        :param v: Value, in hex
        :type v: str
        """
        self.contents.append(v)
        logg.debug('content is now {}'.format(self.contents))


    def uint256(self, v):
        """Parse value as uint256.

        :param v: Value, in hex
        :type v: str
        :rtype: int
        :returns: Int value
        """
        return int(v, 16)


    def bytes32(self, v):
        """Parse value as bytes32.

        :param v: Value, in hex
        :type v: str
        :rtype: str
        :returns: Value, in hex
        """
        return v


    def bool(self, v):
        """Parse value as bool.

        :param v: Value, in hex
        :type v: str
        :rtype: bool
        :returns: Value
        """
        return bool(self.uint256(v))


    def boolean(self, v):
        """Alias of chainlib.eth.contract.ABIContractDecoder.bool
        """
        return bool(self.uint256(v))


    def address(self, v):
        """Parse value as address.

        :param v: Value, in hex
        :type v: str
        :rtype: str
        :returns: Value. in hex
        """
        a = strip_0x(v)[64-40:]
        return to_checksum_address(a)


    def string(self, v):
        """Parse value as string.

        :param v: Value, in hex
        :type v: str
        :rtype: str
        :returns: Value
        """
        s = strip_0x(v)
        b = bytes.fromhex(s)
        cursor = 0
        offset = int.from_bytes(b[cursor:cursor+32], 'big')
        cursor += 32
        length = int.from_bytes(b[cursor:cursor+32], 'big')
        cursor += 32
        content = b[cursor:cursor+length]
        logg.debug('parsing string offset {} length {} content {}'.format(offset, length, content))
        return content.decode('utf-8')


    def __log_typ(self):
        logg.debug('types set to ({})'.format(','.join(self.types)))


    def decode(self):
        """Apply decoder on value array using argument type array.

        :rtype: list
        :returns: List of decoded values
        """
        r = []
        logg.debug('contents {}'.format(self.contents))
        for i in range(len(self.types)):
            m = getattr(self, self.types[i])
            s = self.contents[i]
            r.append(m(s))
        return r


    def get(self):
        """Alias of chainlib.eth.contract.ABIContractDecoder.decode
        """
        return self.decode()


    def __str__(self):
        return self.decode()


class ABIContractLogDecoder(ABIMethodEncoder, ABIContractDecoder):
    """Decoder utils for log entries of an Ethereum network transaction receipt.

    Uses chainlib.eth.contract.ABIContractDecoder.decode to render output from template.
    """
    def __init__(self):
        super(ABIContractLogDecoder, self).__init__()
        self.method_name = None
        self.indexed_content = []


    def topic(self, event):
        """Set topic to match.

        :param event: Topic name
        :type event: str
        """
        self.method(event)


    def get_method_signature(self):
        """Generate topic signature from set topic.

        :rtype: str
        :returns: Topic signature, in hex
        """
        s = self.get_method()
        return keccak256_string_to_hex(s)


    def typ(self, v):
        """Add type to event argument array.

        :param v: Type
        :type v: chainlib.eth.contract.ABIContractType
        """
        super(ABIContractLogDecoder, self).typ(v)
        self.types.append(v.value)


    def apply(self, topics, data):
        """Set log entry data to parse.

        After set, self.decode can be used to render the output.

        :param topics: The topics array of the receipt, list of hex
        :type topics: list
        :param data: Non-indexed data, in hex
        :type data: str
        :raises ValueError: Topic of input does not match topic set in parser
        """
        t = self.get_method_signature()
        if topics[0] != t:
            raise ValueError('topic mismatch')
        for i in range(len(topics) - 1):
            self.contents.append(topics[i+1])
        self.contents += data
              

class ABIContractEncoder(ABIMethodEncoder):

    def __log_latest(self, v):
        l = len(self.types) - 1 
        logg.debug('Encoder added {} -> {} ({})'.format(v, self.contents[l], self.types[l].value))


    def uint256(self, v):
        """Encode value to uint256 and add to input value vector.

        :param v: Integer value
        :type v: int
        """
        v = int(v)
        b = v.to_bytes(32, 'big')
        self.contents.append(b.hex())
        self.types.append(ABIContractType.UINT256)
        self.__log_latest(v)


    def bool(self, v):
        """Alias of chainlib.eth.contract.ABIContractEncoder.boolean.
        """
        return self.boolean(v)


    def boolean(self, v):
        """Encode value to boolean and add to input value vector.

        :param v: Trueish or falsish value
        :type v: any
        :rtype: See chainlib.eth.contract.ABIContractEncoder.uint256
        :returns: See chainlib.eth.contract.ABIContractEncoder.uint256
        """
        if bool(v):
            return self.uint256(1)
        return self.uint256(0)


    def address(self, v):
        """Encode value to address and add to input value vector.

        :param v: Ethereum address, in hex
        :type v: str
        """
        self.bytes_fixed(32, v, 20)
        self.types.append(ABIContractType.ADDRESS)
        self.__log_latest(v)


    def bytes32(self, v):
        """Encode value to bytes32 and add to input value vector.

        :param v: Bytes, in hex
        :type v: str
        """
        self.bytes_fixed(32, v)
        self.types.append(ABIContractType.BYTES32)
        self.__log_latest(v)


    def bytes4(self, v):
        """Encode value to bytes4 and add to input value vector.

        :param v: Bytes, in hex
        :type v: str
        """
        self.bytes_fixed(4, v)
        self.types.append(ABIContractType.BYTES4)
        self.__log_latest(v)



    def string(self, v):
        """Encode value to string and add to input value vector.

        :param v: String input
        :type v: str
        """
        b = v.encode('utf-8')
        l = len(b)
        contents = l.to_bytes(32, 'big')
        contents += b
        padlen = 32 - (l % 32)
        contents += padlen * b'\x00'
        self.bytes_fixed(len(contents), contents)
        self.types.append(ABIContractType.STRING)
        self.__log_latest(v)
        return contents


    def bytes_fixed(self, mx, v, exact=0):
        """Add arbirary length byte data to value vector.

        :param mx: Max length of input data.
        :type mx: int
        :param v: Byte input, hex or bytes
        :type v: str | bytes
        :param exact: Fail parsing if input does not translate to given byte length.
        :type exact: int
        :raises ValueError: Input length or input format mismatch.
        """
        typ = type(v).__name__
        if typ == 'str':
            v = strip_0x(v)
            l = len(v)
            if exact > 0 and l != exact * 2:
                raise ValueError('value wrong size; expected {}, got {})'.format(mx, l))
            if l > mx * 2:
                raise ValueError('value too long ({})'.format(l))
            v = pad(v, mx)
        elif typ == 'bytes':
            l = len(v)
            if exact > 0 and l != exact:
                raise ValueError('value wrong size; expected {}, got {})'.format(mx, l))
            b = bytearray(mx)
            b[mx-l:] = v
            v = pad(b.hex(), mx)
        else:
            raise ValueError('invalid input {}'.format(typ))
        self.contents.append(v.ljust(64, '0'))

    
    def get_method_signature(self):
        """Return abi encoded signature of currently set method.
        """
        s = self.get_method()
        if s == '':
            return s
        return keccak256_string_to_hex(s)[:8]


    def get_contents(self):
        """Encode value array.

        :rtype: str
        :returns: ABI encoded values, in hex
        """
        direct_contents = ''
        pointer_contents = ''
        l = len(self.types)
        pointer_cursor = 32 * l
        for i in range(l):
            if self.types[i] in dynamic_contract_types:
                content_length = len(self.contents[i])
                pointer_contents += self.contents[i]
                direct_contents += pointer_cursor.to_bytes(32, 'big').hex()
                pointer_cursor += int(content_length / 2)
            else:
                direct_contents += self.contents[i]
        s = ''.join(direct_contents + pointer_contents)
        for i in range(0, len(s), 64):
            l = len(s) - i
            if l > 64:
                l = 64
            logg.debug('code word {} {}'.format(int(i / 64), s[i:i+64]))
        return s


    def get(self):
        """Alias of chainlib.eth.contract.ABIContractEncoder.encode
        """
        return self.encode()


    def encode(self):
        """Encode method and value array.

        The data generated by this method is the literal data used as input to contract calls or transactions.

        :rtype: str
        :returns: ABI encoded contract input data, in hex
        """
        m = self.get_method_signature()
        c = self.get_contents()
        return m + c


    def __str__(self):
        return self.encode()



def abi_decode_single(typ, v):
    """Convenience function to decode a single ABI encoded value against a given type.

    :param typ: Type to parse value as
    :type typ: chainlib.eth.contract.ABIContractEncoder
    :param v: Value to parse, in hex
    :type v: str
    """
    d = ABIContractDecoder()
    d.typ(typ)
    d.val(v)
    r = d.decode()
    return r[0]


def code(address, block_spec=BlockSpec.LATEST, id_generator=None):
    """Generate json-rpc query to retrieve code stored at an Ethereum address.

    :param address: Address to use for query, in hex
    :type address: str
    :param block_spec: Block height spec
    :type block_spec: chainlib.block.BlockSpec
    :param id_generator: json-rpc id generator
    :type id_generator: chainlib.jsonrpc.JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    block_height = None
    if block_spec == BlockSpec.LATEST:
        block_height = 'latest'
    elif block_spec == BlockSpec.PENDING:
        block_height = 'pending'
    else:
        block_height = int(block_spec)
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getCode'
    o['params'].append(address)
    o['params'].append(block_height)
    return j.finalize(o)
