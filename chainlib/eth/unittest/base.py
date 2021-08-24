# standard imports
import os
import logging

# external imports
import eth_tester
import coincurve
from chainlib.connection import (
        RPCConnection,
        error_parser,
        )
from chainlib.eth.address import (
        to_checksum_address,        
        )
from chainlib.jsonrpc import (
        jsonrpc_response,
        jsonrpc_error,
        jsonrpc_result,
        )
from hexathon import (
        unpad,
        add_0x,
        strip_0x,
        )

from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer
from crypto_dev_signer.encoding import private_key_to_address


logg = logging.getLogger().getChild(__name__)

test_pk = bytes.fromhex('5087503f0a9cc35b38665955eb830c63f778453dd11b8fa5bd04bc41fd2cc6d6')


class EthTesterSigner(eth_tester.EthereumTester):

    def __init__(self, backend, keystore):
        super(EthTesterSigner, self).__init__(backend)
        logg.debug('accounts {}'.format(self.get_accounts()))
        
        self.keystore = keystore
        self.backend = backend
        self.backend.add_account(test_pk)
        for pk in self.backend.account_keys:
            pubk = pk.public_key
            address = pubk.to_checksum_address()
            logg.debug('test keystore have pk {} pubk {} addr {}'.format(pk, pk.public_key, address))
            self.keystore.import_raw_key(pk._raw_key)


    def new_account(self):
        pk = os.urandom(32)
        address = self.keystore.import_raw_key(pk)
        checksum_address = add_0x(to_checksum_address(address))
        self.backend.add_account(pk)
        return checksum_address


class TestRPCConnection(RPCConnection):

    def __init__(self, location, backend, signer):
        super(TestRPCConnection, self).__init__(location)
        self.backend = backend
        self.signer = signer


    def do(self, o, error_parser=error_parser):
        logg.debug('testrpc do {}'.format(o)) 
        m = getattr(self, o['method'])
        if m == None:
            raise ValueError('unhandled method {}'.format(o['method']))
        r = None
        try:
            result = m(o['params'])
            logg.debug('result {}'.format(result))
            r = jsonrpc_response(o['id'], result)
        except Exception as e:
            logg.exception(e)
            r = jsonrpc_error(o['id'], message=str(e))
        return jsonrpc_result(r, error_parser)


    def eth_blockNumber(self, p):
        block = self.backend.get_block_by_number('latest')
        return block['number']


    def eth_getBlockByNumber(self, p):
        b = bytes.fromhex(strip_0x(p[0]))
        n = int.from_bytes(b, 'big')
        block = self.backend.get_block_by_number(n)
        return block


    def eth_getBlockByHash(self, p):
        block = self.backend.get_block_by_hash(p[0])
        return block


    def eth_getTransactionByBlock(self, p):
        block = self.eth_getBlockByHash(p)
        try:
            tx_index = int(p[1], 16)
        except TypeError:
            tx_index = int(p[1])
        tx_hash = block['transactions'][tx_index]
        tx = self.eth_getTransactionByHash([tx_hash])
        return tx

    def eth_getBalance(self, p):
        balance = self.backend.get_balance(p[0])
        hx = balance.to_bytes(32, 'big').hex()
        return add_0x(unpad(hx))


    def eth_getTransactionCount(self, p):
        nonce = self.backend.get_nonce(p[0])
        hx = nonce.to_bytes(4, 'big').hex()
        return add_0x(unpad(hx))


    def eth_getTransactionByHash(self, p):
        tx = self.backend.get_transaction_by_hash(p[0])
        return tx


    def eth_getTransactionByBlockHashAndIndex(self, p):
        #logg.debug('p {}'.format(p))
        #block = self.eth_getBlockByHash(p[0])
        #tx = block.transactions[p[1]]
        #return eth_getTransactionByHash(tx[0])
        return self.eth_getTransactionByBlock(p)


    def eth_getTransactionReceipt(self, p):
        rcpt = self.backend.get_transaction_receipt(p[0])
        if rcpt.get('block_number') == None:
            rcpt['block_number'] = rcpt['blockNumber']
        else:
            rcpt['blockNumber'] = rcpt['block_number']
        return rcpt


    def eth_getCode(self, p):
        r = self.backend.get_code(p[0])
        return r


    def eth_call(self, p):
        tx_ethtester = to_ethtester_call(p[0])
        r = self.backend.call(tx_ethtester)
        return r


    def eth_gasPrice(self, p):
        return hex(1000000000)


    def personal_newAccount(self, passphrase):
        a = self.backend.new_account()
        return a


    def eth_sign(self, p):
        r = self.signer.sign_ethereum_message(strip_0x(p[0]), strip_0x(p[1]))
        return r


    def eth_sendRawTransaction(self, p):
        r = self.backend.send_raw_transaction(p[0])
        return r


    def eth_signTransaction(self, p):
        raise NotImplementedError('needs transaction deserializer for EIP155Transaction')
        tx_dict = p[0]
        tx = EIP155Transaction(tx_dict, tx_dict['nonce'], tx_dict['chainId'])
        passphrase = p[1]
        r = self.signer.sign_transaction_to_wire(tx, passphrase)
        return r


    def __verify_signer(self, tx, passphrase=''):
        pk_bytes = self.backend.keystore.get(tx.sender)
        pk = coincurve.PrivateKey(secret=pk_bytes)
        result_address = private_key_to_address(pk)
        assert strip_0x(result_address) == strip_0x(tx.sender)


    def sign_transaction(self, tx, passphrase=''):
        self.__verify_signer(tx, passphrase)
        return self.signer.sign_transaction(tx, passphrase)


    def sign_transaction_to_wire(self, tx, passphrase=''):
        self.__verify_signer(tx, passphrase)
        return self.signer.sign_transaction_to_wire(tx, passphrase)


    def disconnect(self):
        pass


def to_ethtester_call(tx):
    if tx['gas'] == '':
        tx['gas'] = '0x00'
    
    if tx['gasPrice'] == '':
        tx['gasPrice'] = '0x00'
    
    tx = {
            'to': tx['to'],
            'from': tx['from'],
            'gas': int(tx['gas'], 16),
            'gas_price': int(tx['gasPrice'], 16),
            'data': tx['data'],
            }
    return tx
