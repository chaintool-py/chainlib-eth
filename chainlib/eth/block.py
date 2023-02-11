# standard imports
import logging
import datetime

# external imports
from chainlib.jsonrpc import JSONRPCRequest
from chainlib.block import Block as BaseBlock
from hexathon import (
        add_0x,
        strip_0x,
        compact,
        to_int as hex_to_int,
        )

# local imports
from chainlib.eth.tx import Tx
from .src import Src

logg = logging.getLogger(__name__)


def block_latest(id_generator=None):
    """Implements chainlib.interface.ChainInterface method
    """
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_blockNumber'
    return j.finalize(o)


def block_by_hash(hsh, include_tx=True, id_generator=None):
    """Implements chainlib.interface.ChainInterface method
    """
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getBlockByHash'
    o['params'].append(hsh)
    o['params'].append(include_tx)
    return j.finalize(o)


def block_by_number(n, include_tx=True, id_generator=None):
    """Implements chainlib.interface.ChainInterface method
    """
    hx = strip_0x(hex(n))
    nhx = add_0x(compact(hx), compact_value=True)
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getBlockByNumber'
    o['params'].append(nhx)
    o['params'].append(include_tx)
    return j.finalize(o)


def transaction_count(block_hash, id_generator=None):
    """Generate json-rpc query to get transaction count of block

    :param block_hash: Block hash, in hex
    :type block_hash: str
    :param id_generator: JSONRPC id generator
    :type id_generator: JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getBlockTransactionCountByHash'
    o['params'].append(block_hash)
    return j.finalize(o)


def syncing(id_generator=None):
    """Request the syncing state of the node

    :param id_generator: JSONRPC id generator
    :type id_generator: JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_syncing'
    return j.finalize(o)


class Block(BaseBlock, Src):
    """Encapsulates an Ethereum block

    :param src: Block representation data
    :type src: dict
    :todo: Add hex to number parse to normalize
    """
   
    tx_generator = Tx

    def __init__(self, src=None, dialect_filter=None):
        super(Block, self).__init__(src=src, dialect_filter=dialect_filter)


    def load_src(self, dialect_filter=None):
        if dialect_filter != None:
            dialect_filter.apply_block(self)

        self.set_hash(self.src['hash'])
        try:
            self.number = int(strip_0x(self.src['number']), 16)
        except TypeError:
            self.number = int(self.src['number'])
        self.txs = self.src['transactions']
        self.block_src = self.src
        try:
            self.timestamp = int(strip_0x(self.src['timestamp']), 16)
        except TypeError:
            self.timestamp = int(self.src['timestamp'])

        try:
            self.author = self.src['author']
        except KeyError:
            self.author = self.src['miner']

        self.fee_limit = self.src['gas_limit']
        self.fee_cost = self.src['gas_used']
        self.parent_hash = self.src['parent_hash']



    def tx_index_by_hash(self, tx_hash):
        i = 0
        idx = -1
        tx_hash = add_0x(tx_hash)
        for tx in self.txs:
            tx_hash_block = None
            try:
                tx_hash_block = add_0x(tx['hash'])
            except TypeError:
                tx_hash_block = add_0x(tx)
            if tx_hash_block == tx_hash:
                idx = i
                break
            i += 1
        if idx == -1:
            raise AttributeError('tx {} not found in block {}'.format(tx_hash, self.hash))
        return idx


    def to_human(self):
        s = """hash: {}
number: {}
parent: {}
timestamp: {}
time: {}
author: {}
gas_limit: {}
gas_used: {}
txs: {}
""".format(
    self.hash,
    self.number,
    self.parent_hash,
    self.timestamp,
    datetime.datetime.fromtimestamp(self.timestamp),
    self.author,
    hex_to_int(self.fee_limit),
    hex_to_int(self.fee_cost),
    len(self.txs),
        )

        return s

