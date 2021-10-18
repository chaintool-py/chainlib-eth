# standard imports
import os
import socket
import unittest
import unittest.mock
import logging
import json

# external imports
from funga.eth.transaction import EIP155Transaction
from funga.eth.signer.defaultsigner import EIP155Signer
from funga.eth.keystore.dict import DictKeystore

# local imports
import chainlib
from chainlib.eth.connection import EthUnixSignerConnection
from chainlib.eth.sign import sign_transaction
from chainlib.eth.tx import TxFactory
from chainlib.eth.address import (
        to_checksum_address,
        is_same_address,
        )
from chainlib.jsonrpc import (
        jsonrpc_response,
        jsonrpc_error,
        )
from hexathon import (
        add_0x,
        )
from chainlib.chain import ChainSpec

from tests.base import TestBase

logging.basicConfig(level=logging.DEBUG)
logg = logging.getLogger()

keystore = DictKeystore() 
alice = keystore.new()
bob = keystore.new()


class Mocket(socket.socket):
  
    req_id = None
    error = False
    tx = None
    signer = None

    def connect(self, v):
        return self


    def send(self, v):
        o = json.loads(v)
        logg.debug('mocket received {}'.format(v))
        Mocket.req_id = o['id']
        params = o['params'][0]
        from_address = to_checksum_address(params.get('from'))
        if not is_same_address(alice, from_address):
            logg.error('from {} does not match alice {}'.format(from_address, alice)) #params))
            Mocket.error = True
        to_address = to_checksum_address(params.get('to'))
        if not is_same_address(bob, to_address):
            logg.error('to {} does not match bob {}'.format(to_address, bob)) #params))
            Mocket.error = True
        if not Mocket.error:
            Mocket.tx = EIP155Transaction(params, params['nonce'], params['chainId'])
            logg.debug('mocket {}'.format(Mocket.tx))
        return len(v)
  

    def recv(self, c):
        if Mocket.req_id != None:

            o = None
            if Mocket.error:
                o = jsonrpc_error(Mocket.req_id)
            else:
                tx = Mocket.tx
                r = Mocket.signer.sign_transaction_to_rlp(tx)
                Mocket.tx = None
                o = jsonrpc_response(Mocket.req_id, add_0x(r.hex()))
            Mocket.req_id = None
            return json.dumps(o).encode('utf-8')

        return b''


class TestSign(TestBase):

    
    def setUp(self):
        super(TestSign, self).__init__()
        self.chain_spec = ChainSpec('evm', 'foo', 42)


        logg.debug('alice {}'.format(alice))
        logg.debug('bob {}'.format(bob))

        self.signer = EIP155Signer(keystore)

        Mocket.signer = self.signer
    

    def test_sign_build(self):
        with unittest.mock.patch('chainlib.connection.socket.socket', Mocket) as m:
            rpc = EthUnixSignerConnection('foo', chain_spec=self.chain_spec)
            f = TxFactory(self.chain_spec, signer=rpc)
            tx = f.template(alice, bob, use_nonce=True)
            tx = f.build(tx)
            logg.debug('tx result {}'.format(tx))

  
    def test_sign_rpc(self):
        with unittest.mock.patch('chainlib.connection.socket.socket', Mocket) as m:
            rpc = EthUnixSignerConnection('foo')
            f = TxFactory(self.chain_spec, signer=rpc)
            tx = f.template(alice, bob, use_nonce=True)
            tx_o = sign_transaction(tx)
            rpc.do(tx_o)


if __name__ == '__main__':
    unittest.main()
