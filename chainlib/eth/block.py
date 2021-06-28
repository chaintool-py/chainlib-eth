# third-party imports
from chainlib.jsonrpc import JSONRPCRequest
from chainlib.eth.tx import Tx
from hexathon import (
        add_0x,
        strip_0x,
        even,
        )


def block_latest(id_generator=None):
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_blockNumber'
    return j.finalize(o)


def block_by_hash(hsh, include_tx=True, id_generator=None):
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getBlockByHash'
    o['params'].append(hsh)
    o['params'].append(include_tx)
    return j.finalize(o)


def block_by_number(n, include_tx=True, id_generator=None):
    nhx = add_0x(even(hex(n)[2:]))
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getBlockByNumber'
    o['params'].append(nhx)
    o['params'].append(include_tx)
    return j.finalize(o)


def transaction_count(block_hash, id_generator=None):
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_getBlockTransactionCountByHash'
    o['params'].append(block_hash)
    return j.finalize(o)


class Block:
    
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


    def src(self):
        return self.block_src


    def tx(self, i):
        return Tx(self.txs[i], self)


    def tx_src(self, i):
        return self.txs[i]


    def __str__(self):
        return 'block {} {} ({} txs)'.format(self.number, self.hash, len(self.txs))


    @staticmethod
    def from_src(src):
        return Block(src)
