# standard imports
import logging

# external imports
from hexathon import (
        add_0x,
        strip_0x,
        )
from crypto_dev_signer.eth.transaction import EIP155Transaction

# local imports
from chainlib.fee import FeeOracle
from chainlib.hash import keccak256_hex_to_hex
from chainlib.jsonrpc import JSONRPCRequest
from chainlib.eth.tx import (
        TxFactory,
        TxFormat,
        raw,
        )
from chainlib.eth.jsonrpc import to_blockheight_param
from chainlib.block import BlockSpec
from chainlib.eth.constant import (
        MINIMUM_FEE_UNITS,
    )

logg = logging.getLogger(__name__)


def price(id_generator=None):
    """Generate json-rpc query to retrieve current network gas price guess from node.

    :param id_generator: json-rpc id generator 
    :type id_generator: chainlib.connection.JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_gasPrice'
    return j.finalize(o)


def balance(address, id_generator=None, height=BlockSpec.LATEST):
    """Generate json-rpc query to retrieve gas balance of address.

    :param address: Address to query balance for, in hex
    :type address: str
    :param id_generator: json-rpc id generator 
    :type id_generator: chainlib.connection.JSONRPCIdGenerator
    :param height: Block height specifier
    :type height: chainlib.block.BlockSpec
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getBalance'
    o['params'].append(address)
    height = to_blockheight_param(height)
    o['params'].append(height)
    return j.finalize(o)


def parse_balance(balance):
    """Parse result of chainlib.eth.gas.balance rpc query

    :param balance: rpc result value, in hex or int
    :type balance: any
    :rtype: int
    :returns: Balance integer value
    """
    try:
        r = int(balance, 10)
    except ValueError:
        r = int(balance, 16)
    return r


class Gas(TxFactory):
    """Gas transaction helper.
    """

    def create(self, sender_address, recipient_address, value, data=None, tx_format=TxFormat.JSONRPC, id_generator=None):
        """Generate json-rpc query to execute gas transaction.

        See parent class TxFactory for details on output format and general usage.

        :param sender_address: Sender address, in hex
        :type sender_address: str
        :param recipient_address: Recipient address, in hex
        :type recipient_address: str
        :param value: Value of transaction, integer decimal value (wei)
        :type value: int
        :param data: Arbitrary input data, in hex. None means no data (vanilla gas transaction).
        :type data: str
        :param tx_format: Output format
        :type tx_format: chainlib.eth.tx.TxFormat
        """
        tx = self.template(sender_address, recipient_address, use_nonce=True)
        tx['value'] = value
        if data != None:
            tx['data'] = data
        txe = EIP155Transaction(tx, tx['nonce'], tx['chainId'])
        tx_raw = self.signer.sign_transaction_to_wire(txe)
        tx_raw_hex = add_0x(tx_raw.hex())
        tx_hash_hex = add_0x(keccak256_hex_to_hex(tx_raw_hex))

        o = None
        if tx_format == TxFormat.JSONRPC:
            o = raw(tx_raw_hex, id_generator=id_generator)
        elif tx_format == TxFormat.RLP_SIGNED:
            o = tx_raw_hex

        return (tx_hash_hex, o)



class RPCGasOracle(FeeOracle):
    """JSON-RPC only gas parameter helper.

    :param conn: RPC connection
    :type conn: chainlib.connection.RPCConnection
    :param code_callback: Callback method to evaluate gas usage for method and inputs.
    :type code_callback: method taking abi encoded input data as single argument
    :param min_price: Override gas price if less than given value
    :type min_price: int
    :param id_generator: json-rpc id generator 
    :type id_generator: chainlib.connection.JSONRPCIdGenerator
    """

    def __init__(self, conn, code_callback=None, min_price=1, id_generator=None):
        super(RPCGasOracle, self).__init__(code_callback=code_callback)
        self.conn = conn
        self.min_price = min_price
        self.id_generator = id_generator


    def get_fee(self, code=None, input_data=None):
        """Retrieve gas parameters from node.

        If code is given, the set code callback will be used to estimate gas usage.

        If code is not given or code callback is not set, the chainlib.eth.constant.MINIMUM_FEE_UNITS constant will be used. This gas limit will only be enough gas for a gas transaction without input data.

        :param code: EVM execution code to evaluate against, in hex
        :type code: str
        :param input_data: Contract input data, in hex
        :type input_data: str
        :rtype: tuple
        :returns: Gas price in wei, and gas limit in gas units
        """
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

    
    def get_gas(self, code=None, input_data=None):
        return self.get_fee(code=code, input_data=input_data)


class RPCPureGasOracle(RPCGasOracle):
    """Convenience constructor for rpc gas oracle without minimum price.

    :param conn: RPC connection
    :type conn: chainlib.connection.RPCConnection
    :param code_callback: Callback method to evaluate gas usage for method and inputs.
    :type code_callback: method taking abi encoded input data as single argument
    :param id_generator: json-rpc id generator 
    :type id_generator: chainlib.connection.JSONRPCIdGenerator
    """
    def __init__(self, conn, code_callback=None, id_generator=None):
        super(RPCPureGasOracle, self).__init__(conn, code_callback=code_callback, min_price=0, id_generator=id_generator)


class OverrideGasOracle(RPCGasOracle):
    """Gas parameter helper that can be selectively overridden.

    If both price and limit are set, the conn parameter will not be used.

    If either price or limit is set to None, the rpc in the conn value will be used to query the missing value.

    If both are None, behaves the same as chainlib.eth.gas.RPCGasOracle. 

    :param price: Set exact gas price
    :type price: int
    :param limit: Set exact gas limit
    :type limit: int
    :param conn: RPC connection for fallback query
    :type conn: chainlib.connection.RPCConnection
    :param code_callback: Callback method to evaluate gas usage for method and inputs.
    :type code_callback: method taking abi encoded input data as single argument
    :param id_generator: json-rpc id generator 
    :type id_generator: chainlib.connection.JSONRPCIdGenerator
    """
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
        

    def get_fee(self, code=None, input_data=None):
        r = None
        fee_units = None
        fee_price = None

        rpc_results = super(OverrideGasOracle, self).get_fee(code)
 
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


    def get_gas(self, code=None, input_data=None):
        return self.get_fee(code=code, input_data=input_data)


DefaultGasOracle = RPCGasOracle
