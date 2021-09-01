# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import sys
import os
import json
import argparse
import logging
import enum
import select

# external imports
from potaahto.symbols import snake_and_camel
from hexathon import (
        add_0x,
        strip_0x,
        )
import sha3
from chainlib.jsonrpc import (
        JSONRPCRequest,
        jsonrpc_result,
        IntSequenceGenerator,
        )
from chainlib.chain import ChainSpec
from chainlib.status import Status

# local imports
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.tx import (
        Tx,
        pack,
        )
from chainlib.eth.address import (
        to_checksum_address,
        is_checksum_address,
        )
from chainlib.eth.block import (
        Block,
        block_by_hash,
        )
from chainlib.eth.runnable.util import decode_for_puny_humans
from chainlib.eth.jsonrpc import to_blockheight_param
import chainlib.eth.cli

logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s')
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.eth.cli.argflag_std_read
argparser = chainlib.eth.cli.ArgumentParser(arg_flags)
argparser.add_positional('item', type=str, help='Address or transaction to retrieve data for')
args = argparser.parse_args()
config = chainlib.eth.cli.Config.from_args(args, arg_flags, default_config_dir=config_dir)

rpc = chainlib.eth.cli.Rpc()
conn = rpc.connect_by_config(config)

chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))

item = add_0x(args.item)


def get_transaction(conn, tx_hash, id_generator):
    j = JSONRPCRequest(id_generator=id_generator)
    o = j.template()
    o['method'] = 'eth_getTransactionByHash'
    o['params'].append(tx_hash)
    o = j.finalize(o)
    tx_src = conn.do(o)
    if tx_src == None:
        logg.error('Transaction {} not found'.format(tx_hash))
        sys.exit(1)

    if config.true('_RAW'):
        tx_src = Tx.src_normalize(tx_src)
        return pack(tx_src, chain_spec).hex()

    tx = None
    status = -1
    rcpt = None

    o = j.template()
    o['method'] = 'eth_getTransactionReceipt'
    o['params'].append(tx_hash)
    o = j.finalize(o)
    rcpt = conn.do(o)
    #status = int(strip_0x(rcpt['status']), 16)

    if tx == None:
        tx = Tx(tx_src)
    if rcpt != None:
        tx.apply_receipt(rcpt)
        rcpt = snake_and_camel(rcpt)
        o = block_by_hash(rcpt['block_hash'])
        r = conn.do(o)
        block = Block(r)
        tx.apply_block(block)
    logg.debug('foo {}'.format(tx_src))
    tx.generate_wire(chain_spec)
    return tx
    


def get_address(conn, address, id_generator, height):
    j = JSONRPCRequest(id_generator=id_generator)
    o = j.template()
    o['method'] = 'eth_getCode'
    o['params'].append(address)
    height = to_blockheight_param(height)
    o['params'].append(height)
    o = j.finalize(o)
    code = conn.do(o)
    
    content = strip_0x(code, allow_empty=True)
    if len(content) == 0:
        return None

    return content


def main():
    address = item
    r = None
    if len(address) > 42:
        r = get_transaction(conn, address, rpc.id_generator)
        if not config.true('_RAW'):
            r = r.to_human()
    else:
        if config.get('_UNSAFE'):
            address = to_checksum_address(address)
        elif not is_checksum_address(address):
            raise ValueError('invalid checksum address: {}'.format(address))
        r = get_address(conn, address, rpc.id_generator, config.get('_HEIGHT'))
    if r != None:
        print(r)


if __name__ == '__main__':
    main()
