#!python3

"""Data retrieval script

.. moduleauthor:: Louis Holbrook <dev@holbrook.no>
.. pgp:: 0826EDA1702D1E87C6E2875121D2E7BB88C2A746 

"""

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
from hexathon import (
        add_0x,
        strip_0x,
        )
import sha3

# local imports
from chainlib.eth.address import to_checksum
from chainlib.jsonrpc import (
        JSONRPCRequest,
        jsonrpc_result,
        IntSequenceGenerator,
        )
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.tx import (
        Tx,
        pack,
        )
from chainlib.eth.address import to_checksum_address
from chainlib.eth.block import Block
from chainlib.chain import ChainSpec
from chainlib.status import Status
from chainlib.eth.runnable.util import decode_for_puny_humans

logging.basicConfig(level=logging.WARNING, format='%(asctime)s %(levelname)s %(filename)s:%(lineno)d %(message)s')
logg = logging.getLogger()

default_eth_provider = os.environ.get('RPC_PROVIDER')
if default_eth_provider == None:
    default_eth_provider = os.environ.get('ETH_PROVIDER', 'http://localhost:8545')

def stdin_arg(t=0):
    h = select.select([sys.stdin], [], [], t)
    if len(h[0]) > 0:
        v = h[0][0].read()
        return v.rstrip()
    return None

argparser = argparse.ArgumentParser('eth-get', description='display information about an Ethereum address or transaction', epilog='address/transaction can be provided as an argument or from standard input')
argparser.add_argument('-p', '--provider', dest='p', default=default_eth_provider, type=str, help='Web3 provider url (http only)')
argparser.add_argument('-i', '--chain-spec', dest='i', type=str, default='evm:ethereum:1', help='Chain specification string')
argparser.add_argument('--rlp', action='store_true', help='Display transaction as raw rlp')
argparser.add_argument('--seq', action='store_true', help='Use sequential rpc ids')
argparser.add_argument('-u', '--unsafe', dest='u', action='store_true', help='Auto-convert address to checksum adddress')
argparser.add_argument('-v', action='store_true', help='Be verbose')
argparser.add_argument('-vv', action='store_true', help='Be more verbose')
argparser.add_argument('item', nargs='?', default=stdin_arg(), type=str, help='Item to get information for (address og transaction)')
args = argparser.parse_args()

if args.vv:
    logg.setLevel(logging.DEBUG)
elif args.v:
    logg.setLevel(logging.INFO)

argp = args.item
if argp == None:
    argp = stdin_arg(None)
    if argsp == None:
        argparser.error('need first positional argument or value from stdin')

rpc_id_generator = None
if args.seq:
    rpc_id_generator = IntSequenceGenerator()

auth = None
if os.environ.get('RPC_AUTHENTICATION') == 'basic':
    from chainlib.auth import BasicAuth
    auth = BasicAuth(os.environ['RPC_USERNAME'], os.environ['RPC_PASSWORD'])
conn = EthHTTPConnection(args.p, auth=auth)

chain_spec = ChainSpec.from_chain_str(args.i)

item = add_0x(args.item)
as_rlp = bool(args.rlp)


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

    if as_rlp:
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
    tx.generate_wire(chain_spec)
    return tx


def get_address(conn, address, id_generator):
    j = JSONRPCRequest(id_generator=id_generator)
    o = j.template()
    o['method'] = 'eth_getCode'
    o['params'].append(address)
    o['params'].append('latest')
    o = j.finalize(o)
    code = conn.do(o)
    
    content = strip_0x(code, allow_empty=True)
    if len(content) == 0:
        return None

    return content


def main():
    r = None
    if len(item) > 42:
        r = get_transaction(conn, item, rpc_id_generator).to_human()
    elif args.u or to_checksum_address(item):
        r = get_address(conn, item, rpc_id_generator)
    print(r)


if __name__ == '__main__':
    main()
