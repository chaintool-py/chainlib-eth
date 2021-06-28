# local imports
from chainlib.error import ExecutionError

class EthException(Exception):
    pass


class RevertEthException(EthException, ExecutionError):
    pass


class NotFoundEthException(EthException):
    pass


class RequestMismatchException(EthException):
    pass


class DefaultErrorParser:

    def translate(self, error):
        return EthException('default parser code {}'.format(error))
