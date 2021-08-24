# external imports
from hexathon import (
        add_0x,
        strip_0x,
        )

# local imports
from chainlib.nonce import NonceOracle as BaseNonceOracle
from chainlib.jsonrpc import JSONRPCRequest


def nonce(address, confirmed=False, id_generator=None):
    """Generate json-rpc query to retrieve next nonce of address from node.

    :param address: Address to retrieve nonce for, in hex
    :type address: str
    :param id_generator: json-rpc id generator 
    :type id_generator: chainlib.connection.JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getTransactionCount'
    o['params'].append(address)
    if confirmed:
        o['params'].append('latest')
    else:
        o['params'].append('pending')
    return j.finalize(o)


def nonce_confirmed(address, id_generator=None):
    return nonce(address, confirmed=True, id_generator=id_generator)


class NonceOracle(BaseNonceOracle):
    """Base class for the nonce parameter helpers.

    :param address: Address to retireve nonce for, in hex
    :type address: str
    :param id_generator: json-rpc id generator 
    :type id_generator: chainlib.connection.JSONRPCIdGenerator
    """
    def __init__(self, address, id_generator=None):
        self.id_generator = id_generator
        super(NonceOracle, self).__init__(address)


    def get_nonce(self):
        """Load initial nonce value.
        """
        raise NotImplementedError('Class must be extended')


    def next_nonce(self):
        """Return next nonce value and advance.

        :rtype: int
        :returns: Next nonce for address.
        """
        n = self.nonce
        self.nonce += 1
        return n


class RPCNonceOracle(NonceOracle):
    """JSON-RPC only nonce parameter helper.

    :param address: Address to retireve nonce for, in hex
    :type address: str
    :param conn: RPC connection
    :type conn: chainlib.connection.RPCConnection
    :param id_generator: json-rpc id generator 
    :type id_generator: chainlib.connection.JSONRPCIdGenerator
    """
    def __init__(self, address, conn, id_generator=None):
        self.conn = conn
        super(RPCNonceOracle, self).__init__(address, id_generator=id_generator)


    def get_nonce(self):
        """Load and return nonce value from network.

        Note! First call to next_nonce after calling get_nonce will return the same value!

        :rtype: int
        :returns: Initial nonce
        """
        o = nonce(self.address, id_generator=self.id_generator)
        r = self.conn.do(o)
        n = strip_0x(r)
        return int(n, 16)


class OverrideNonceOracle(NonceOracle):
    """Manually set initial nonce value.

    :param address: Address to retireve nonce for, in hex
    :type address: str
    :param nonce: Nonce value
    :type nonce: int
    :param id_generator: json-rpc id generator (not used)
    :type id_generator: chainlib.connection.JSONRPCIdGenerator
    """
    def __init__(self, address, nonce, id_generator=None):
        self.initial_nonce = nonce
        self.nonce = self.initial_nonce
        super(OverrideNonceOracle, self).__init__(address, id_generator=id_generator)


    def get_nonce(self):
        """Returns initial nonce value set at object construction.

        :rtype: int
        :returns: Initial nonce value.
        """
        return self.initial_nonce


DefaultNonceOracle = RPCNonceOracle
