# external imports
from chainlib.jsonrpc import JSONRPCRequest
from chainlib.block import Block as BaseBlock
from hexathon import (
        add_0x,
        strip_0x,
        even,
        )

# local imports
from chainlib.eth.tx import Tx


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
    nhx = add_0x(even(hex(n)[2:]))
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


class Block(BaseBlock):
    """Encapsulates an Ethereum block

    :param src: Block representation data
    :type src: dict
    :todo: Add hex to number parse to normalize
    """
   
    tx_generator = Tx

    def __init__(self, src):
        self.hash = src['hash']
        try:
            self.number = int(strip_0x(src['number']), 16)
        except TypeError:
            self.number = int(src['number'])
        self.txs = src['transactions']
        self.block_src = src
        try:
            self.timestamp = int(strip_0x(src['timestamp']), 16)
        except TypeError:
            self.timestamp = int(src['timestamp'])


    def get_tx(self, tx_hash):
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

