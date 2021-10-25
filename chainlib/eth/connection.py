# standard imports
import copy
import logging
import json
import datetime
import time
import socket
from urllib.request import (
        Request,
        urlopen,
        )

# third-party imports
from hexathon import (
        add_0x,
        strip_0x,
        )

# local imports
from .error import RevertEthException
from chainlib.eth.dialect import DefaultErrorParser
from .sign import (
        sign_transaction,
        )
from chainlib.connection import (
        ConnType,
        RPCConnection,
        JSONRPCHTTPConnection,
        JSONRPCUnixConnection,
        error_parser,
        )
from chainlib.jsonrpc import (
        JSONRPCRequest,
        jsonrpc_result,
        )
from chainlib.eth.tx import (
        unpack,
        )
from potaahto.symbols import snake_and_camel

logg = logging.getLogger(__name__)


class EthHTTPConnection(JSONRPCHTTPConnection):
    """HTTP Interface for Ethereum node JSON-RPC

    :todo: support https
    """

    def wait(self, tx_hash_hex, delay=0.5, timeout=0.0, error_parser=error_parser, id_generator=None):
        """Poll for confirmation of a transaction on network.

        Returns the result of the transaction if it was successfully executed on the network, and raises RevertEthException if execution fails.

        This is a blocking call.

        :param tx_hash_hex: Transaction hash to wait for, hex
        :type tx_hash_hex: str
        :param delay: Polling interval
        :type delay: float
        :param timeout: Max time to wait for confirmation (0 = no timeout)
        :type timeout: float
        :param error_parser: json-rpc response error parser
        :type error_parser: chainlib.jsonrpc.ErrorParser
        :param id_generator: json-rpc id generator
        :type id_generator: chainlib.jsonrpc.JSONRPCIdGenerator
        :raises TimeoutError: Timeout reached
        :raises chainlib.eth.error.RevertEthException: Transaction confirmed but failed
        :rtype: dict
        :returns: Transaction receipt
        """
        t = datetime.datetime.utcnow()
        i = 0
        while True:
            j = JSONRPCRequest(id_generator)
            o = j.template()
            o['method'] ='eth_getTransactionReceipt'
            o['params'].append(add_0x(tx_hash_hex))
            o = j.finalize(o)
            req = Request(
                    self.location,
                    method='POST',
                    )
            req.add_header('Content-Type', 'application/json')
            data = json.dumps(o)
            logg.debug('({}) poll receipt attempt {} {}'.format(str(self), i, data))
            res = urlopen(req, data=data.encode('utf-8'))
            r = json.load(res)

            e = jsonrpc_result(r, error_parser)
            if e != None:
                e = snake_and_camel(e)
                # In openethereum we encounter receipts that have NONE block hashes and numbers. WTF...
                if e['block_hash'] == None:
                    logg.warning('poll receipt attempt {} returned receipt but with a null block hash value!'.format(i))
                else:
                    logg.debug('({}) poll receipt completed {}'.format(str(self), r))
                    logg.debug('e {}'.format(strip_0x(e['status'])))
                    if strip_0x(e['status']) == '00':
                        raise RevertEthException(tx_hash_hex)
                    return e

            if timeout > 0.0:
                delta = (datetime.datetime.utcnow() - t) + datetime.timedelta(seconds=delay)
                if  delta.total_seconds() >= timeout:
                    raise TimeoutError(tx_hash)

            time.sleep(delay)
            i += 1


    def __str__(self):
        return 'ETH HTTP JSONRPC'


    def check_rpc(self, id_generator=None):
        """Execute Ethereum specific json-rpc query to (superficially) check whether node is sane.

        :param id_generator: json-rpc id generator
        :type id_generator: chainlib.jsonrpc.JSONRPCIdGenerator
        :raises Exception: Any exception indicates an invalid node
        """
        j = JSONRPCRequest(id_generator)
        req = j.template()
        req['method'] = 'net_version'
        req = j.finalize(req)
        r = self.do(req)
 

class EthUnixConnection(JSONRPCUnixConnection):
    """Unix socket implementation of Ethereum JSON-RPC
    """

    def wait(self, tx_hash_hex, delay=0.5, timeout=0.0, error_parser=error_parser):
        """See EthHTTPConnection. Not yet implemented for unix socket.
        """
        raise NotImplementedError('Not yet implemented for unix socket')


def sign_transaction_to_rlp(chain_spec, doer, tx):
    """Generate a signature query and execute it against a json-rpc signer backend.

    Uses the `eth_signTransaction` json-rpc method, generated by chainlib.eth.sign.sign_transaction.

    :param chain_spec: Chain spec to use for EIP155 signature.
    :type chain_spec: chainlib.chain.ChainSpec
    :param doer: Signer rpc backend
    :type doer: chainlib.connection.RPCConnection implementing json-rpc
    :param tx: Transaction object
    :type tx: dict
    :rtype: bytes
    :returns: Ethereum signature
    """
    txs = tx.serialize()
    logg.debug('serializing {}'.format(txs))
    # TODO: because some rpc servers may fail when chainId is included, we are forced to spend cpu here on this
    chain_id = txs.get('chainId') or 1
    if chain_spec != None:
        chain_id = chain_spec.chain_id()
    txs['chainId'] = add_0x(chain_id.to_bytes(2, 'big').hex())
    txs['from'] = add_0x(tx.sender)
    o = sign_transaction(txs)
    r = doer(o)
    logg.debug('sig got {}'.format(r))
    return bytes.fromhex(strip_0x(r))


def sign_message(doer, msg):
    """Sign arbitrary data using the Ethereum message signer protocol.

    :param doer: Signer rpc backend
    :type doer: chainlib.connection.RPCConnection with json-rpc
    :param msg: Message to sign, in hex
    :type msg: str
    :rtype: str
    :returns: Signature, hex
    """
    o = sign_message(msg)
    return doer(o)


class EthUnixSignerConnection(EthUnixConnection):
    """Connects rpc signer methods to Unix socket connection interface
    """
   
    def sign_transaction_to_wire(self, tx):
        """Sign transaction using unix socket rpc.

        :param tx: Transaction object
        :type tx: dict 
        :rtype: See chainlib.eth.connection.sign_transaction_to_rlp
        :returns: Serialized signature
        """
        return sign_transaction_to_rlp(self.chain_spec, self.do, tx)


    def sign_message(self, msg):
        """Sign message using unix socket json-rpc.

        :param msg: Message to sign, in hex
        :type msg: str
        :rtype: See chainlin.eth.connection.sign_message
        :returns: See chainlin.eth.connection.sign_message
        """
        return sign_message(self.do, msg)


class EthHTTPSignerConnection(EthHTTPConnection):
   
    def sign_transaction_to_wire(self, tx):
        """Sign transaction using http json-rpc.

        :param tx: Transaction object
        :type tx: dict 
        :rtype: See chainlin.eth.connection.sign_transaction_to_rlp
        :returns: Serialized signature
        """
        return sign_transaction_to_rlp(self.chain_spec, self.do, tx)


    def sign_message(self, tx):
        """Sign message using http json-rpc.

        :param msg: Message to sign, in hex
        :type msg: str
        :rtype: See chainlin.eth.connection.sign_message
        :returns: See chainlin.eth.connection.sign_message
        """
        return sign_message(self.do, tx)



RPCConnection.register_constructor(ConnType.HTTP, EthHTTPConnection, tag='eth_default')
RPCConnection.register_constructor(ConnType.HTTP_SSL, EthHTTPConnection, tag='eth_default')
RPCConnection.register_constructor(ConnType.UNIX, EthUnixConnection, tag='eth_default')
