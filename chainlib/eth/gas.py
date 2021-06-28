# standard imports
import logging

# third-party imports
from hexathon import (
        add_0x,
        strip_0x,
        )
from crypto_dev_signer.eth.transaction import EIP155Transaction

# local imports
from chainlib.hash import keccak256_hex_to_hex
from chainlib.jsonrpc import JSONRPCRequest
from chainlib.eth.tx import (
        TxFactory,
        TxFormat,
        raw,
        )
from chainlib.eth.constant import (
        MINIMUM_FEE_UNITS,
    )

logg = logging.getLogger(__name__)


def price(id_generator=None):
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_gasPrice'
    return j.finalize(o)


def balance(address, id_generator=None):
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getBalance'
    o['params'].append(address)
    o['params'].append('latest')
    return j.finalize(o)


def parse_balance(balance):
    try:
        r = int(balance, 10)
    except ValueError:
        r = int(balance, 16)
    return r


class Gas(TxFactory):

    def create(self, sender_address, recipient_address, value, tx_format=TxFormat.JSONRPC, id_generator=None):
        tx = self.template(sender_address, recipient_address, use_nonce=True)
        tx['value'] = value
        txe = EIP155Transaction(tx, tx['nonce'], tx['chainId'])
        tx_raw = self.signer.sign_transaction_to_rlp(txe)
        tx_raw_hex = add_0x(tx_raw.hex())
        tx_hash_hex = add_0x(keccak256_hex_to_hex(tx_raw_hex))

        o = None
        if tx_format == TxFormat.JSONRPC:
            o = raw(tx_raw_hex, id_generator=id_generator)
        elif tx_format == TxFormat.RLP_SIGNED:
            o = tx_raw_hex

        return (tx_hash_hex, o)



class RPCGasOracle:

    def __init__(self, conn, code_callback=None, min_price=1, id_generator=None):
        self.conn = conn
        self.code_callback = code_callback
        self.min_price = min_price
        self.id_generator = id_generator


    def get_gas(self, code=None):
        gas_price = 0
        if self.conn != None:
            o = price(id_generator=self.id_generator)
            r = self.conn.do(o)
            n = strip_0x(r)
            gas_price = int(n, 16)
        fee_units = MINIMUM_FEE_UNITS
        if self.code_callback != None:
            fee_units = self.code_callback(code)
        if gas_price < self.min_price:
            logg.debug('adjusting price {} to set minimum {}'.format(gas_price, self.min_price))
            gas_price = self.min_price
        return (gas_price, fee_units)


class RPCPureGasOracle(RPCGasOracle):

    def __init__(self, conn, code_callback=None, id_generator=None):
        super(RPCPureGasOracle, self).__init__(conn, code_callback=code_callback, min_price=0, id_generator=id_generator)


class OverrideGasOracle(RPCGasOracle):

    def __init__(self, price=None, limit=None, conn=None, code_callback=None, id_generator=None):
        self.conn = None
        self.code_callback = None
        self.limit = limit
        self.price = price

        price_conn = None

        if self.limit == None or self.price == None:
            if self.price == None:
                price_conn = conn
            logg.debug('override gas oracle with rpc fallback; price {} limit {}'.format(self.price, self.limit))

        super(OverrideGasOracle, self).__init__(price_conn, code_callback, id_generator=id_generator)
        

    def get_gas(self, code=None):
        r = None
        fee_units = None
        fee_price = None

        rpc_results = super(OverrideGasOracle, self).get_gas(code)
 
        if self.limit != None:
            fee_units = self.limit
        if self.price != None:
            fee_price = self.price

        if fee_price == None:
            if rpc_results != None:
                fee_price = rpc_results[0]
                logg.debug('override gas oracle without explicit price, setting from rpc {}'.format(fee_price))
            else:
                fee_price = MINIMUM_FEE_PRICE
                logg.debug('override gas oracle without explicit price, setting default {}'.format(fee_price))
        if fee_units == None:
            if rpc_results != None:
                fee_units = rpc_results[1]
                logg.debug('override gas oracle without explicit limit, setting from rpc {}'.format(fee_units))
            else:
                fee_units = MINIMUM_FEE_UNITS
                logg.debug('override gas oracle without explicit limit, setting default {}'.format(fee_units))
        
        return (fee_price, fee_units)


DefaultGasOracle = RPCGasOracle
