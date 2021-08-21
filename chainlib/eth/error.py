# local imports
from chainlib.error import ExecutionError


class EthException(Exception):
    """Base class for all Ethereum related errors.
    """
    pass


class RevertEthException(EthException, ExecutionError):
    """Raised when an rpc call or transaction reverts.
    """
    pass


class NotFoundEthException(EthException):
    """Raised when rpc query is made against an identifier that is not known by the node.
    """
    pass


class RequestMismatchException(EthException):
    """Raised when a request data parser is given unexpected input data.
    """
    pass


class DefaultErrorParser:
    """Generate eth specific exception for the default json-rpc query error parser.
    """
    def translate(self, error):
        return EthException('default parser code {}'.format(error))
