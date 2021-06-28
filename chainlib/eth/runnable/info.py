#!python3

"""Token balance query script

.. moduleauthor:: Louis Holbrook <dev@holbrook.no>
.. pgp:: 0826EDA1702D1E87C6E2875121D2E7BB88C2A746 

"""

# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import datetime
import sys
import os
import json
import argparse
import logging

# third-party imports
from hexathon import (
        add_0x,
        strip_0x,
        even,
        )
import sha3
from eth_abi import encode_single

# local imports
from chainlib.eth.address import (
        to_checksum_address,
        is_checksum_address,
        )
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
from chainlib.jsonrpc import (
        IntSequenceGenerator,
        )
from chainlib.chain import ChainSpec

BLOCK_SAMPLES = 10

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

default_eth_provider = os.environ.get('RPC_PROVIDER')
if default_eth_provider == None:
    default_eth_provider = os.environ.get('ETH_PROVIDER', 'http://localhost:8545')

argparser = argparse.ArgumentParser()
argparser.add_argument('-p', '--provider', dest='p', default=default_eth_provider, type=str, help='Web3 provider url (http only)')
argparser.add_argument('-i', '--chain-spec', dest='i', type=str, default='evm:ethereum:1', help='Chain specification string')
argparser.add_argument('-H', '--human', dest='human', action='store_true', help='Use human-friendly formatting')
argparser.add_argument('-u', '--unsafe', dest='u', action='store_true', help='Auto-convert address to checksum adddress')
argparser.add_argument('-l', '--long', dest='l', action='store_true', help='Calculate averages through sampling of blocks and txs')
argparser.add_argument('-v', action='store_true', help='Be verbose')
argparser.add_argument('--seq', action='store_true', help='Use sequential rpc ids')
argparser.add_argument('-vv', action='store_true', help='Be more verbose')
argparser.add_argument('-y', '--key-file', dest='y', type=str, help='Include summary for keyfile')
argparser.add_argument('address', nargs='?', type=str, help='Include summary for address (conflicts with -y)')
args = argparser.parse_args()


if args.vv:
    logg.setLevel(logging.DEBUG)
elif args.v:
    logg.setLevel(logging.INFO)

signer = None
holder_address = None
if args.address != None:
    if not args.u and not is_checksum_address(args.address):
        raise ValueError('invalid checksum address {}'.format(args.address))
    holder_address = add_0x(args.address)
elif args.y != None:
    f = open(args.y, 'r')
    o = json.load(f)
    f.close()
    holder_address = add_0x(to_checksum_address(o['address']))

rpc_id_generator = None
if args.seq:
    rpc_id_generator = IntSequenceGenerator()

auth = None
if os.environ.get('RPC_AUTHENTICATION') == 'basic':
    from chainlib.auth import BasicAuth
    auth = BasicAuth(os.environ['RPC_USERNAME'], os.environ['RPC_PASSWORD'])
conn = EthHTTPConnection(args.p, auth=auth)

gas_oracle = OverrideGasOracle(conn)

token_symbol = 'eth'

chain_spec = ChainSpec.from_chain_str(args.i)

human = args.human

longmode = args.l

def main():
    o = network_id(id_generator=rpc_id_generator)
    r = conn.do(o)
    #if human:
    #    n = format(n, ',')
    sys.stdout.write('Network id: {}\n'.format(r))

    o = block_latest(id_generator=rpc_id_generator)
    r = conn.do(o)
    n = int(r, 16)
    first_block_number = n
    if human:
        n = format(n, ',')
    sys.stdout.write('Block: {}\n'.format(n))

    o = block_by_number(first_block_number, False, id_generator=rpc_id_generator)
    r = conn.do(o)
    last_block = Block(r)
    last_timestamp = last_block.timestamp

    if longmode:
        aggr_time = 0.0
        aggr_gas = 0
        for i in range(BLOCK_SAMPLES): 
            o = block_by_number(first_block_number-i, False, id_generator=rpc_id_generator)
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

    o = price(id_generator=rpc_id_generator)
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
