# external imports

# local imports
from chainlib.eth.error import EthException
from chainlib.dialect import DialectFilter


class DefaultErrorParser:
    """Generate eth specific exception for the default json-rpc query error parser.
    """
    def translate(self, error):
        return EthException('default parser code {}'.format(error))


class DefaultDialectFilter(DialectFilter):

    def apply_src(self, src):
        try:
            inpt = src['input']
        except KeyError:
            inpt = src['data']
            src['input'] = src['data']
        return src
