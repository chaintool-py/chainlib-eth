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
        transaction,
        receipt,
        )
from chainlib.eth.address import (
        to_checksum_address,
        is_checksum_address,
        )
from chainlib.eth.block import (
        Block,
        block_by_hash,
        )
from chainlib.eth.jsonrpc import to_blockheight_param
import chainlib.eth.cli
from chainlib.eth.cli.arg import (
        Arg,
        ArgFlag,
        process_args,
        stdin_arg,
        )
from chainlib.eth.cli.config import (
        Config,
        process_config,
        )
from chainlib.eth.contract import code
from chainlib.eth.cli.log import process_log
from chainlib.eth.settings import process_settings


logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')


def process_config_local(config, arg, args, flags):
    item = config.get('_POSARG')
    try:
        item = strip_0x(item)
    except TypeError:
        item = stdin_arg()
        item = strip_0x(item)

    config.add(item, '_ITEM', False)
    return config


def process_settings_local(settings, config):
    item = config.get('_ITEM')
    if len(item) == 40:
        config.add(item, '_RECIPIENT', False)
    elif len(item) == 64:
        config.add(item, '_HASH', False)

    return process_settings(settings, config)


arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.STD_BASE_READ | arg_flags.TARGET | arg_flags.TAB
flags = arg_flags.less(flags, arg_flags.CHAIN_SPEC)

argparser = chainlib.eth.cli.ArgumentParser()
argparser = process_args(argparser, arg, flags)
argparser.add_argument('item', type=str, help='Address or transaction to retrieve data for')
args = argparser.parse_args()

logg = process_log(args, logg)

config = Config()
config = process_config(config, arg, args, flags, positional_name='item')
config = process_config_local(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainSettings()
settings = process_settings_local(settings, config)
logg.debug('settings loaded:\n{}'.format(settings))


def get_transaction(conn, chain_spec, tx_hash, id_generator):
    o = transaction(tx_hash, id_generator=id_generator)
    tx_src = conn.do(o)
    if tx_src == None:
        logg.error('Transaction {} not found'.format(tx_hash))
        sys.exit(1)

    if config.true('_RAW') and config.get('_OUTARG') == None:
        tx_src = Tx.src_normalize(tx_src)
        return pack(tx_src, chain_spec).hex()

    tx = None
    status = -1
    rcpt = None

    o = receipt(tx_hash, id_generator=id_generator)
    rcpt = conn.do(o)

    if tx == None:
        tx = Tx(tx_src)
    if rcpt != None:
        tx.apply_receipt(rcpt)
        rcpt = snake_and_camel(rcpt)
        o = block_by_hash(rcpt['block_hash'])
        r = conn.do(o)
        block = Block(r, dialect_filter=settings.get('RPC_DIALECT_FILTER'))
        tx.apply_block(block)
    tx.generate_wire(chain_spec)
    return tx
    


def get_address(conn, address, id_generator, height):
    o = code(address, height, id_generator=id_generator)
    r = conn.do(o)
    
    content = strip_0x(r, allow_empty=True)
    if len(content) == 0:
        return None

    return content


def main():
    r = None
    if settings.get('HASH') != None:
        hsh = settings.get('HASH')[0]
        r = get_transaction(
                settings.get('CONN'),
                settings.get('CHAIN_SPEC'),
                hsh,
                settings.get('RPC_ID_GENERATOR'),
                )
        if not config.true('_RAW') or config.get('_OUTARG') != None:
            r = r.to_human(fields=config.get('_OUTARG'), skip_keys=config.true('_RAW'))
    else:
        r = get_address(
            settings.get('CONN'),
            settings.get('RECIPIENT'),
            settings.get('RPC_ID_GENERATOR'),
            settings.get('HEIGHT'),
            )
    if r != None:
        sys.stdout.write(r)
        if not config.true('_NOLINE'):
            sys.stdout.write('\n')


if __name__ == '__main__':
    main()
