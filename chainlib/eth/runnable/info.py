# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import datetime
import sys
import os
import json
import argparse
import logging

# external imports
from chainlib.chain import ChainSpec
from hexathon import (
        add_0x,
        strip_0x,
        even,
        )
import sha3
from funga.eth.signer import EIP155Signer

# local imports
from chainlib.eth.address import AddressChecksum
from chainlib.eth.chain import network_id
from chainlib.eth.block import (
        block_latest,
        block_by_number,
        syncing,
        Block,
        )
from chainlib.eth.tx import count
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.gas import (
        OverrideGasOracle,
        balance,
        price,
        )
import chainlib.eth.cli

BLOCK_SAMPLES = 10

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

results_translation = {
    'network_id': 'Network Id',
    'block': 'Block',
    'syncing': 'Syncing',
    'gas_limit': 'Gas Limit',
    'gas_price': 'Gas Price',
    'block_time': 'Block time',
        }


arg_flags = chainlib.eth.cli.argflag_std_read
argparser = chainlib.eth.cli.ArgumentParser(arg_flags)
argparser.add_argument('--long', action='store_true', help='Calculate averages through sampling of blocks and txs')
argparser.add_argument('--local', action='store_true', help='Include local info')
argparser.add_positional('entry', required=False, help='Output single item')
args = argparser.parse_args()

extra_args = {
        'local': None,
        'long': None,
        'entry': None,
        }
config = chainlib.eth.cli.Config.from_args(args, arg_flags, extra_args=extra_args, default_config_dir=config_dir)

if config.get('_ENTRY') != None:
    if config.get('_ENTRY') not in results_translation.keys():
        raise ValueError('Unknown entry {}'.format(config.get('_ENTRY')))

rpc = chainlib.eth.cli.Rpc()
conn = rpc.connect_by_config(config)

token_symbol = 'eth'

chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))

human = not config.true('_RAW')

longmode = config.true('_LONG')

def set_result(results, k, v, w=sys.stdout):
    kt = results_translation[k]
    if str(config.get('_ENTRY')) == k:
        w.write('{}'.format(v))
        return True
    logg.info('{}: {}\n'.format(kt, v))
    results[k] = v
    return False


def main():
    results = {}

    o = network_id(id_generator=rpc.id_generator)
    r = conn.do(o)
    #if human:
    #    n = format(n, ',')
    if set_result(results, 'network_id', r):
        return

    o = block_latest(id_generator=rpc.id_generator)
    r = conn.do(o)
    try:
        n = int(r, 16)
    except ValueError:
        n = int(r)
    first_block_number = n
    if human:
        n = format(n, ',')
    if set_result(results, 'block', n):
        return

    o = block_by_number(first_block_number, False, id_generator=rpc.id_generator)
    r = conn.do(o)
    last_block = Block(r)
    last_timestamp = last_block.timestamp

    if longmode:
        aggr_time = 0.0
        aggr_gas = 0
        for i in range(BLOCK_SAMPLES): 
            o = block_by_number(first_block_number-i, False, id_generator=rpc.id_generator)
            r = conn.do(o)
            block = Block(r)
            aggr_time += last_block.timestamp - block.timestamp
        
            gas_limit = int(r['gasLimit'], 16)
            aggr_gas += gas_limit

            last_block = block
            last_timestamp = block.timestamp

        n = int(aggr_gas / BLOCK_SAMPLES)
        if human:
            n = format(n, ',')

        if set_result(results, 'gas_limit', n):
            return
        if set_result(results, 'block_time', aggr_time / BLOCK_SAMPLES):
            return

    o = price(id_generator=rpc.id_generator)
    r = conn.do(o)
    n = int(r, 16)
    if human:
        n = format(n, ',')
    if set_result(results, 'gas_price', n):
        return

    if config.get('_LOCAL'):
        o = syncing()
        r = conn.do(o)
        if set_result(results, 'syncing', r):
            return

    if config.get('_ENTRY') != None:
        raise RuntimeError('entry {} ({}) not processed, please review the flag settings'.format(config.get('_ENTRY'), results_translation[config.get('_ENTRY')]))

    for k in results.keys():
        kt = results_translation[k]
        sys.stdout.write('{}: {}\n'.format(kt, results[k]))


if __name__ == '__main__':
    main()
