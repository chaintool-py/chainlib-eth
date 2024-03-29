# standard imports
import enum
import re
import logging

# external imports
from hexathon import (
        strip_0x,
        add_0x,
        pad,
        same as same_hex,
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
    UINT128 = 'uint128'
    UINT64 = 'uint64'
    UINT32 = 'uint32'
    UINT16 = 'uint16'
    UINT8 = 'uint8'
    ADDRESS = 'address'
    STRING = 'string'
    BYTES = 'bytes'
    BOOLEAN = 'bool'
    TUPLE = 'tuple'

dynamic_contract_types = [
    ABIContractType.STRING,
    ABIContractType.BYTES,
    ]

pointer_contract_types = [
    ABIContractType.TUPLE,
        ] + dynamic_contract_types


class ABIContract:
    """Base class for Ethereum smart contract encoder
    """
    def __init__(self):
        self.types = []
        self.contents = []
        self.dirty = False


    def add_type(self, v):
        self.types.append(v)
        self.dirty = True


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
        contents = '(' + ','.join(self.method_contents) + ')'
        if self.method_name == None:
            return contents
        return self.method_name + contents


    def typ(self, v):
        """Add argument type to argument vector.

        Method name must be set before this is called.

        :param v: Type to add
        :type v: chainlib.eth.contract.ABIContractType
        :raises AttributeError: Type set before method name
        :raises TypeError: Invalid type
        """
        if isinstance(v, ABIContractEncoder):
            return self.typ_tuple(v)
        if not isinstance(v, ABIContractType):
            raise TypeError('method type not valid; expected {}, got {}'.format(type(ABIContractType).__name__, type(v).__name__))
        self.method_contents.append(v.value)
        self.__log_method()


    def typ_literal(self, v):
        if type(v).__name__ != 'str':
            raise ValueError('literal type must be string')
        self.method_contents.append(v)
        self.__log_method()


    def typ_tuple(self, v):
        if not isinstance(v, ABIContractEncoder):
            raise TypeError('tuple type not valid; expected {}, got {}'.format(type(ABIContractEncoder).__name__, type(v).__name__))
        r = v.get_method()
        self.method_contents.append(r)
        self.__log_method()


    def __log_method(self):
        logg.debug('method set to {}'.format(self.get_method()))


    def get_signature(self):
        """Generate topic signature from set topic.

        :rtype: str
        :returns: Topic signature, in hex
        """
        if self.method_name == None:
            return ''
        s = self.get_method()
        return keccak256_string_to_hex(s)


    def get_method_signature(self):
        s = self.get_signature()
        if s == '':
            return s
        return s[:8]



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
        if v == ABIContractType.TUPLE:
            raise NotImplementedError('sorry, tuple decoding not yet implemented')
        self.add_type(v.value)
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


    def uintn(self, v, bitsize):
        # all uints no matter what size are returned to 256 bit boundary
        return self.uint256(v)

        l = len(v) * 8 * 2
        if bitsize % 8 > 0:
            raise ValueError('must be 8 multiple')
        elif bitsize > 256:
            raise ValueError('max 256 bits')
        elif l < bitsize:
            raise ValueError('input value length {} shorter than bitsize {}'.format(l, bitsize))
        return int(v[:int(bitsize/8)], 16)


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
            m = None
            try:
                m = getattr(self, self.types[i])
                logg.debug('executing module {}'.format(m))
                s = self.contents[i]
                r.append(m(s))
            except AttributeError as e:
                if len(self.types[i]) > 4 and self.types[i][:4] == 'uint':
                    m = getattr(self, 'uintn')
                    s = self.contents[i]
                    v = m(s, int(self.types[i][4:]))
                    r.append(v)
                else:
                    raise e

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

    def typ(self, v):
        """Add type to event argument array.

        :param v: Type
        :type v: chainlib.eth.contract.ABIContractType
        """
        super(ABIContractLogDecoder, self).typ(v)
        self.add_type(v.value)



    def apply(self, topics, data):
        """Set log entry data to parse.

        After set, self.decode can be used to render the output.

        :param topics: The topics array of the receipt, list of hex
        :type topics: list
        :param data: Non-indexed data, in hex
        :type data: str
        :raises ValueError: Topic of input does not match topic set in parser
        """
        t = self.get_signature()
        if not same_hex(topics[0], t):
            raise ValueError('topic mismatch')
        for i in range(len(topics) - 1):
            self.contents.append(topics[i+1])
        self.contents += data


    # Backwards compatibility
    def get_method_signature(self):
        logg.warning('ABIContractLogDecoder.get_method_signature() is deprecated. Use ABIContractLogDecoder.get_signature() instead')
        return self.get_signature()
              

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
        self.add_type(ABIContractType.UINT256)
        self.__log_latest(v)


    def uintn(self, v, bitsize):
        """Encode value to uint256 and add to input value vector.

        :param v: Integer value
        :type v: int
        """
        if bitsize % 8 > 0:
            raise ValueError('must be 8 multiple')
        elif bitsize > 256:
            raise ValueError('max 256 bits')

        # encodings of all uint types are padded to word boundary
        return self.uint256(v)

        v = int(v)
        b = v.to_bytes(int(bitsize / 8), 'big')
        self.contents.append(b.hex())
        typ = getattr(ABIContractType, 'UINT' + str(bitsize))
        self.add_type(typ)
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
        self.bytes_fixed(32, v, exact=20)
        self.add_type(ABIContractType.ADDRESS)
        self.__log_latest(v)


    def bytes32(self, v):
        """Encode value to bytes32 and add to input value vector.

        :param v: Bytes, in hex
        :type v: str
        """
        self.bytes_fixed(32, v)
        self.add_type(ABIContractType.BYTES32)
        self.__log_latest(v)


    def bytes4(self, v):
        """Encode value to bytes4 and add to input value vector.

        :param v: Bytes, in hex
        :type v: str
        """
        self.bytes_fixed(4, v)
        self.add_type(ABIContractType.BYTES4)
        self.__log_latest(v)


    def tuple(self, v):
        if type(v).__name__ != 'ABIContractEncoder':
            raise ValueError('Type for tuple must be ABIContractEncoder')
        r = v.get_contents()
        self.bytes_fixed(int(len(r) / 2), r)
        self.add_type(ABIContractType.TUPLE)
        self.__log_latest(v)


    def string(self, v):
        """Encode value to string and add to input value vector.

        :param v: String input
        :type v: str
        """
        b = v.encode('utf-8')
        return self._bytes(b, pad=True)


    def bytes(self, v):
        b = bytes.fromhex(v)
        return self._bytes(b, pad=True)
        

    def _bytes(self, v, pad=False):
        l = len(v)
        contents = l.to_bytes(32, 'big')
        contents += v
        padlen = 32 - (l % 32)
        if pad:
            contents += padlen * b'\x00'
        self.bytes_fixed(len(contents), contents)
        self.add_type(ABIContractType.STRING)
        self.__log_latest(v)
        return contents


    def bytes_fixed(self, mx, v, exact=0, enforce_word=False):
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
            if mx == 0:
                mx = l
            if exact > 0 and l != exact * 2:
                raise ValueError('value wrong size; expected {}, got {})'.format(mx, l))
            if enforce_word and mx % 32 > 0:
                raise ValueError('value size {} does not match word boundary'.format(mx))
            if l > mx * 2:
                raise ValueError('value too long ({})'.format(l))
            v = pad(v, mx)
        elif typ == 'bytes':
            l = len(v)
            if mx == 0:
                mx = l
            if exact > 0 and l != exact:
                raise ValueError('value wrong size; expected {}, got {})'.format(mx, l))
            if enforce_word and mx % 32 > 0:
                raise ValueError('value size {} does not match word boundary'.format(mx))
            b = bytearray(mx)
            b[mx-l:] = v
            v = pad(b.hex(), mx)
        else:
            raise ValueError('invalid input {}'.format(typ))
        self.contents.append(v.ljust(64, '0'))


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
            if self.types[i] in pointer_contract_types:
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
        self.dirty = False
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
        block_height = block_height.to_bytes(8, byteorder='big')
        block_height = add_0x(block_height.hex())
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getCode'
    o['params'].append(address)
    o['params'].append(block_height)
    return j.finalize(o)
