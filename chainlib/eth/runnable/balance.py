#!python3

"""Token balance query script

.. moduleauthor:: Louis Holbrook <dev@holbrook.no>
.. pgp:: 0826EDA1702D1E87C6E2875121D2E7BB88C2A746 

"""

# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
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

# local imports
from chainlib.eth.address import to_checksum
from chainlib.jsonrpc import (
        jsonrpc_result,
        IntSequenceGenerator,
        )
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.gas import (
        OverrideGasOracle,
        balance,
        )
from chainlib.chain import ChainSpec

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

default_eth_provider = os.environ.get('RPC_PROVIDER')
if default_eth_provider == None:
    default_eth_provider = os.environ.get('ETH_PROVIDER', 'http://localhost:8545')

argparser = argparse.ArgumentParser()
argparser.add_argument('-p', '--provider', dest='p', default=default_eth_provider, type=str, help='Web3 provider url (http only)')
argparser.add_argument('-i', '--chain-spec', dest='i', type=str, default='evm:ethereum:1', help='Chain specification string')
argparser.add_argument('-u', '--unsafe', dest='u', action='store_true', help='Auto-convert address to checksum adddress')
argparser.add_argument('--seq', action='store_true', help='Use sequential rpc ids')
argparser.add_argument('-v', action='store_true', help='Be verbose')
argparser.add_argument('-vv', action='store_true', help='Be more verbose')
argparser.add_argument('address', type=str, help='Account address')
args = argparser.parse_args()


if args.vv:
    logg.setLevel(logging.DEBUG)
elif args.v:
    logg.setLevel(logging.INFO)

rpc_id_generator = None
if args.seq:
    rpc_id_generator = IntSequenceGenerator()

auth = None
if os.environ.get('RPC_AUTHENTICATION') == 'basic':
    from chainlib.auth import BasicAuth
    auth = BasicAuth(os.environ['RPC_USERNAME'], os.environ['RPC_PASSWORD'])
conn = EthHTTPConnection(args.p, auth=auth)

gas_oracle = OverrideGasOracle(conn)

address = to_checksum(args.address)
if not args.u and address != add_0x(args.address):
    raise ValueError('invalid checksum address')

chain_spec = ChainSpec.from_chain_str(args.i)

def main():
    r = None
    decimals = 18

    o = balance(address, id_generator=rpc_id_generator)
    r = conn.do(o)
   
    hx = strip_0x(r)
    balance_value = int(hx, 16)
    logg.debug('balance {} = {} decimals {}'.format(even(hx), balance_value, decimals))

    balance_str = str(balance_value)
    balance_len = len(balance_str)
    if balance_len < decimals + 1:
        print('0.{}'.format(balance_str.zfill(decimals)))
    else:
        offset = balance_len-decimals
        print('{}.{}'.format(balance_str[:offset],balance_str[offset:]))


if __name__ == '__main__':
    main()
