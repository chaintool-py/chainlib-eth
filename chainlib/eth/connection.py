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
from .error import (
        DefaultErrorParser,
        RevertEthException,
        )
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

logg = logging.getLogger(__name__)


class EthHTTPConnection(JSONRPCHTTPConnection):

    def wait(self, tx_hash_hex, delay=0.5, timeout=0.0, error_parser=error_parser, id_generator=None):
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
            logg.debug('(HTTP) poll receipt attempt {} {}'.format(i, data))
            res = urlopen(req, data=data.encode('utf-8'))
            r = json.load(res)

            e = jsonrpc_result(r, error_parser)
            if e != None:
                logg.debug('(HTTP) poll receipt completed {}'.format(r))
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


    def check_rpc(self, id_generator=None):
        j = JSONRPCRequest(id_generator)
        req = j.template()
        req['method'] = 'net_version'
        req = j.finalize(req)
        r = self.do(req)
 

class EthUnixConnection(JSONRPCUnixConnection):

    def wait(self, tx_hash_hex, delay=0.5, timeout=0.0, error_parser=error_parser):
        raise NotImplementedError('Not yet implemented for unix socket')


def sign_transaction_to_rlp(chain_spec, doer, tx):
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
    o = sign_message(msg)
    return doer(o)


class EthUnixSignerConnection(EthUnixConnection):
   
    def sign_transaction_to_rlp(self, tx):
        return sign_transaction_to_rlp(self.chain_spec, self.do, tx)


    def sign_message(self, tx):
        return sign_message(self.do, tx)


class EthHTTPSignerConnection(EthHTTPConnection):
   
    def sign_transaction_to_rlp(self, tx):
        return sign_transaction_to_rlp(self.chain_spec, self.do, tx)


    def sign_message(self, tx):
        return sign_message(self.do, tx)



RPCConnection.register_constructor(ConnType.HTTP, EthHTTPConnection, tag='eth_default')
RPCConnection.register_constructor(ConnType.HTTP_SSL, EthHTTPConnection, tag='eth_default')
RPCConnection.register_constructor(ConnType.UNIX, EthUnixConnection, tag='eth_default')
