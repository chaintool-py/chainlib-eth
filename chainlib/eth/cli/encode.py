# standard imports
import re
import logging

# external imports
from chainlib.eth.contract import ABIContractType

logg = logging.getLogger(__name__)


class CLIEncoder:

    __re_uint = r'^([uU])[int]*([0-9]+)?$'
    __re_bytes = r'^([bB])[ytes]*([0-9]+)?$'
    __re_string = r'^([sS])[tring]*$'
    __translations = [
            'to_uint',
            'to_bytes',
            'to_string',
            ]

    def to_uint(self, typ):
        s = None
        a = None
        m = re.match(self.__re_uint, typ)
        if m == None:
            return None

        n = m.group(2)
        if m.group(2) == None:
            n = 256
        s = 'UINT256'.format(m.group(2))
        a = getattr(ABIContractType, s)
        return (s, a)


    def to_bytes(self, typ):
        s = None
        a = None
        m = re.match(self.__re_bytes, typ)
        if m == None:
            return None
        
        n = m.group(2)
        if n == None:
            n = 32
        s = 'BYTES{}'.format(n)
        a = getattr(ABIContractType, s)
        return (s, a)


    def to_string(self, typ):
        m = re.match(self.__re_string, typ)
        if m == None:
            return None
        s = 'STRING'
        a = getattr(ABIContractType, s)
        return (s, a)


    def translate_type(self, typ):
        r = None
        for tr in self.__translations:
            r = getattr(self, tr)(typ)
            if r != None:
                break
        if r == None:
            raise ValueError('no translation for type {}'.format(typ))
        logg.debug('type {} translated to {}'.format(typ, r[0]))
        return r[1]
