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
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer

# local imports
from chainlib.eth.address import AddressChecksum
from chainlib.eth.chain import network_id
from chainlib.eth.block import (
        block_latest,
        block_by_number,
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

arg_flags = chainlib.eth.cli.argflag_std_read
argparser = chainlib.eth.cli.ArgumentParser(arg_flags)
argparser.add_positional('address', type=str, help='Address to retrieve info for', required=False)
argparser.add_argument('--long', action='store_true', help='Calculate averages through sampling of blocks and txs')
args = argparser.parse_args()

config = chainlib.eth.cli.Config.from_args(args, arg_flags, extra_args={'long': None}, default_config_dir=config_dir)

holder_address = args.address
wallet = chainlib.eth.cli.Wallet()
wallet.from_config(config)
if wallet.get_signer_address() == None and holder_address != None:
    wallet.from_address(holder_address)

rpc = chainlib.eth.cli.Rpc(wallet=wallet)
conn = rpc.connect_by_config(config)

token_symbol = 'eth'

chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))

human = not config.true('_RAW')

longmode = config.true('_LONG')

def main():
    o = network_id(id_generator=rpc.id_generator)
    r = conn.do(o)
    #if human:
    #    n = format(n, ',')
    sys.stdout.write('Network id: {}\n'.format(r))

    o = block_latest(id_generator=rpc.id_generator)
    r = conn.do(o)
    n = int(r, 16)
    first_block_number = n
    if human:
        n = format(n, ',')
    sys.stdout.write('Block: {}\n'.format(n))

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

        sys.stdout.write('Gaslimit: {}\n'.format(n))
        sys.stdout.write('Blocktime: {}\n'.format(aggr_time / BLOCK_SAMPLES))

    o = price(id_generator=rpc.id_generator)
    r = conn.do(o)
    n = int(r, 16)
    if human:
        n = format(n, ',')
    sys.stdout.write('Gasprice: {}\n'.format(n))

    if holder_address != None:
        o = count(holder_address)
        r = conn.do(o)
        n = int(r, 16)
        sys.stdout.write('Address: {}\n'.format(holder_address))
        sys.stdout.write('Nonce: {}\n'.format(n))


if __name__ == '__main__':
    main()
