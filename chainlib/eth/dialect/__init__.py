# local imports
from chainlib.eth.error import EthException


class DefaultErrorParser:
    """Generate eth specific exception for the default json-rpc query error parser.
    """
    def translate(self, error):
        return EthException('default parser code {}'.format(error))
