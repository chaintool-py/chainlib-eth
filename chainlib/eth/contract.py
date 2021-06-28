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

#logg = logging.getLogger(__name__)
logg = logging.getLogger()


re_method = r'^[a-zA-Z0-9_]+$'

class ABIContractType(enum.Enum):

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

    def __init__(self):
        self.types = []
        self.contents = []


class ABIMethodEncoder(ABIContract):

    def __init__(self):
        super(ABIMethodEncoder, self).__init__()
        self.method_name = None
        self.method_contents = []


    def method(self, m):
        if re.match(re_method, m) == None:
            raise ValueError('Invalid method {}, must match regular expression {}'.format(re_method))
        self.method_name = m
        self.__log_method()


    def get_method(self):
        if self.method_name == None:
            return ''
        return '{}({})'.format(self.method_name, ','.join(self.method_contents))


    def typ(self, v):
        if self.method_name == None:
            raise AttributeError('method name must be set before adding types')
        if not isinstance(v, ABIContractType):
            raise TypeError('method type not valid; expected {}, got {}'.format(type(ABIContractType).__name__, type(v).__name__))
        self.method_contents.append(v.value)
        self.__log_method()


    def __log_method(self):
        logg.debug('method set to {}'.format(self.get_method()))



class ABIContractDecoder(ABIContract):

    
    def typ(self, v):
        if not isinstance(v, ABIContractType):
            raise TypeError('method type not valid; expected {}, got {}'.format(type(ABIContractType).__name__, type(v).__name__))
        self.types.append(v.value)
        self.__log_typ()


    def val(self, v):
        self.contents.append(v)
        logg.debug('content is now {}'.format(self.contents))


    def uint256(self, v):
        return int(v, 16)


    def bytes32(self, v):
        return v


    def bool(self, v):
        return bool(self.uint256(v))


    def boolean(self, v):
        return bool(self.uint256(v))


    def address(self, v):
        a = strip_0x(v)[64-40:]
        return to_checksum_address(a)


    def string(self, v):
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
        r = []
        logg.debug('contents {}'.format(self.contents))
        for i in range(len(self.types)):
            m = getattr(self, self.types[i])
            s = self.contents[i]
            logg.debug('{} {} {} {} {}'.format(i, m, self.types[i], self.contents[i], s))
            #r.append(m(s.hex()))
            r.append(m(s))
        return r


    def get(self):
        return self.decode()


    def __str__(self):
        return self.decode()


class ABIContractLogDecoder(ABIMethodEncoder, ABIContractDecoder):
    
    def __init__(self):
        super(ABIContractLogDecoder, self).__init__()
        self.method_name = None
        self.indexed_content = []


    def topic(self, event):
        self.method(event)


    def get_method_signature(self):
        s = self.get_method()
        return keccak256_string_to_hex(s)


    def typ(self, v):
        super(ABIContractLogDecoder, self).typ(v)
        self.types.append(v.value)


    def apply(self, topics, data):
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
        v = int(v)
        b = v.to_bytes(32, 'big')
        self.contents.append(b.hex())
        self.types.append(ABIContractType.UINT256)
        self.__log_latest(v)


    def bool(self, v):
        return self.boolean(v)


    def boolean(self, v):
        if bool(v):
            return self.uint256(1)
        return self.uint256(0)


    def address(self, v):
        self.bytes_fixed(32, v, 20)
        self.types.append(ABIContractType.ADDRESS)
        self.__log_latest(v)


    def bytes32(self, v):
        self.bytes_fixed(32, v)
        self.types.append(ABIContractType.BYTES32)
        self.__log_latest(v)


    def bytes4(self, v):
        self.bytes_fixed(4, v)
        self.types.append(ABIContractType.BYTES4)
        self.__log_latest(v)



    def string(self, v):
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
        s = self.get_method()
        if s == '':
            return s
        return keccak256_string_to_hex(s)[:8]


    def get_contents(self):
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
        return self.encode()


    def encode(self):
        m = self.get_method_signature()
        c = self.get_contents()
        return m + c


    def __str__(self):
        return self.encode()



def abi_decode_single(typ, v):
    d = ABIContractDecoder()
    d.typ(typ)
    d.val(v)
    r = d.decode()
    return r[0]


def code(address, block_spec=BlockSpec.LATEST, id_generator=None):
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
