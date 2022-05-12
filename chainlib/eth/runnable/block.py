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
        block_by_number,
        )
from chainlib.eth.runnable.util import decode_for_puny_humans
from chainlib.eth.jsonrpc import to_blockheight_param
import chainlib.eth.cli
from chainlib.eth.cli.arg import (
        Arg,
        ArgFlag,
        process_args,
        )
from chainlib.eth.cli.config import (
        Config,
        process_config,
        )
from chainlib.eth.cli.log import process_log

logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

argparser = chainlib.eth.cli.ArgumentParser()
arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.STD_BASE_READ
flags = arg_flags.less(flags, arg_flags.CHAIN_SPEC)
argparser = process_args(argparser, arg, flags)
argparser.add_argument('block', nargs='?', type=str, help='Block hash or number to retrieve')
args = argparser.parse_args()

logg = process_log(args, logg)

config = Config()
config = process_config(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))

rpc = chainlib.eth.cli.Rpc()
conn = rpc.connect_by_config(config)

chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))

item = add_0x(args.block)


def get_block(conn, block_identifier, id_generator):
    maybe_hex = None
    r = None
    try:
        maybe_hex = strip_0x(block_identifier)
    except ValueError:
        r = get_block_number(conn, block_identifier, id_generator)

    if len(maybe_hex) != 64:
        r = get_block_number(conn, block_identifier, id_generator)

    if maybe_hex != block_identifier:
        r = get_block_hash(conn, block_identifier, id_generator)
    else:
        r = get_block_number(conn, block_identifier, id_generator)

    return block_process(r)


def get_block_number(conn, block_number, id_generator):
    block_number = int(block_number)
    o = block_by_number(block_number, include_tx=False)
    block_src = conn.do(o)
    if block_src == None:
        logg.error('Block number {} not found'.format(block_number))
        sys.exit(1)
    return block_src

def get_block_hash(conn, block_hash, id_generator):
    block_hash = add_0x(block_hash)
    o = block_by_hash(block_hash, include_tx=False)
    block_src = conn.do(o)
    if block_src == None:
        logg.error('Block hash {} not found'.format(block_hash))
        sys.exit(1)
    return block_src


def block_process(block_src):
    return Block(block_src)


def main():
    block_identifier = item
    r = get_block(conn, block_identifier, rpc.id_generator)
    if not config.true('_RAW'):
        r = r.to_human()
    else:
        r = repr(r)
    if r != None:
        print(r)


if __name__ == '__main__':
    main()
