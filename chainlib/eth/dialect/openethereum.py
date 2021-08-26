# standard imports
import logging

# local imports
from chainlib.eth.dialect import DefaultErrorParser
from chainlib.error import RPCNonceException

logg = logging.getLogger(__name__)


class DialectErrorParser(DefaultErrorParser):

    def translate(self, error):
        if error['error']['code'] == -32010:
            if 'nonce is too low' in error['error']['message']:
                return RPCNonceException(error)
        return super(DialectErrorParser, self).translate(error)
