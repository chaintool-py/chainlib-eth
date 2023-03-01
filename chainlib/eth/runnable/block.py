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
from chainlib.settings import ChainSettings

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
        block_latest,
        )
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
from chainlib.eth.settings import process_settings

logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

def process_config_local(config, arg, args, flags):
    if len(args.block) > 0:
        config.add(args.block[0], '_BLOCK', False)
    return config


def process_settings_local(settings, config):
    block_identifier = config.get('_POSARG')
    if block_identifier == None:
        return process_settings(settings, config)

    maybe_hex = None
    is_number = False
    try:
        maybe_hex = strip_0x(block_identifier)
    except ValueError:
        is_number = True

    if maybe_hex != None:
        if len(maybe_hex) != 64:
            is_number = True
    else:
        is_number = True

    r = None
    if not is_number:
        config.add(block_identifier, '_HASH', False)
    else:
        settings.set('_BLOCK', int(block_identifier))

    return process_settings(settings, config)


argparser = chainlib.eth.cli.ArgumentParser()
arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.STD_BASE_READ
flags = arg_flags.less(flags, arg_flags.CHAIN_SPEC)
argparser = process_args(argparser, arg, flags)
argparser.add_argument('block', type=str, help='Block hash or number to retrieve')
args = argparser.parse_args()

logg = process_log(args, logg)

config = Config()
config = process_config(config, arg, args, flags, positional_name='block')
config = process_config_local(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainSettings()
settings = process_settings_local(settings, config)
logg.debug('settings loaded:\n{}'.format(settings))



def get_block(settings):
    hsh = None
    try:
        hsh = settings.get('HASH')[0]
    except TypeError:
        pass
    r = None
    if hsh == None:
        r = get_block_number(
                settings.get('CONN'),
                settings.get('_BLOCK'),
                settings.get('RPC_ID_GENERATOR'),
                )
    else:
        r = get_block_hash(
                settings.get('CONN'),
                hsh,
                settings.get('RPC_ID_GENERATOR'),
                )

    return block_process(r)


def get_block_number_latest(conn, id_generator):
    o = block_latest(id_generator)
    r = conn.do(o)
    return int(r, 16)


def get_block_number(conn, block_number, id_generator):
    o = None
    if block_number == None:
        block_number = get_block_number_latest(conn, id_generator)
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
    return Block(block_src, dialect_filter=settings.get('RPC_DIALECT_FILTER'))


def main():
    r = get_block(settings)

    if not config.true('_RAW'):
        r = r.to_human()
    else:
        r = repr(r)
    if r != None:
        print(r)


if __name__ == '__main__':
    main()
