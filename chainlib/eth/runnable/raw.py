#!python3

"""Gas transfer script

.. moduleauthor:: Louis Holbrook <dev@holbrook.no>
.. pgp:: 0826EDA1702D1E87C6E2875121D2E7BB88C2A746 

"""

# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import io
import sys
import os
import json
import argparse
import logging
import urllib

# external imports
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer
from crypto_dev_signer.keystore.dict import DictKeystore
from hexathon import (
        add_0x,
        strip_0x,
        )

# local imports
from chainlib.eth.address import to_checksum
from chainlib.eth.connection import EthHTTPConnection
from chainlib.jsonrpc import (
        JSONRPCRequest,
        IntSequenceGenerator,
        )
from chainlib.eth.nonce import (
        RPCNonceOracle,
        OverrideNonceOracle,
        )
from chainlib.eth.gas import (
        RPCGasOracle,
        OverrideGasOracle,
        )
from chainlib.eth.tx import (
        TxFactory,
        raw,
        )
from chainlib.chain import ChainSpec
from chainlib.eth.runnable.util import decode_for_puny_humans

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

default_eth_provider = os.environ.get('RPC_PROVIDER')
if default_eth_provider == None:
    default_eth_provider = os.environ.get('ETH_PROVIDER', 'http://localhost:8545')

argparser = argparse.ArgumentParser()
argparser.add_argument('-p', '--provider', dest='p', default=default_eth_provider, type=str, help='Web3 provider url (http only)')
argparser.add_argument('-w', action='store_true', help='Wait for the last transaction to be confirmed')
argparser.add_argument('-ww', action='store_true', help='Wait for every transaction to be confirmed')
argparser.add_argument('-i', '--chain-spec', dest='i', type=str, default='evm:ethereum:1', help='Chain specification string')
argparser.add_argument('-y', '--key-file', dest='y', type=str, help='Ethereum keystore file to use for signing')
argparser.add_argument('-u', '--unsafe', dest='u', action='store_true', help='Auto-convert address to checksum adddress')
argparser.add_argument('--env-prefix', default=os.environ.get('CONFINI_ENV_PREFIX'), dest='env_prefix', type=str, help='environment prefix for variables to overwrite configuration')
argparser.add_argument('--nonce', type=int, help='override nonce')
argparser.add_argument('--gas-price', dest='gas_price', type=int, help='override gas price')
argparser.add_argument('--gas-limit', dest='gas_limit', type=int, help='override gas limit')
argparser.add_argument('-a', '--recipient', dest='a', type=str, help='recipient address (None for contract creation)')
argparser.add_argument('-value', type=int, help='gas value of transaction in wei')
argparser.add_argument('--seq', action='store_true', help='Use sequential rpc ids')
argparser.add_argument('-v', action='store_true', help='Be verbose')
argparser.add_argument('-vv', action='store_true', help='Be more verbose')
argparser.add_argument('-s', '--send', dest='s', action='store_true', help='Send to network')
argparser.add_argument('-l', '--local', dest='l', action='store_true', help='Local contract call')
argparser.add_argument('data', nargs='?', type=str, help='Transaction data')
args = argparser.parse_args()


if args.vv:
    logg.setLevel(logging.DEBUG)
elif args.v:
    logg.setLevel(logging.INFO)

block_all = args.ww
block_last = args.w or block_all

passphrase_env = 'ETH_PASSPHRASE'
if args.env_prefix != None:
    passphrase_env = args.env_prefix + '_' + passphrase_env
passphrase = os.environ.get(passphrase_env)
if passphrase == None:
    logg.warning('no passphrase given')
    passphrase=''

signer_address = None
keystore = DictKeystore()
if args.y != None:
    logg.debug('loading keystore file {}'.format(args.y))
    signer_address = keystore.import_keystore_file(args.y, password=passphrase)
    logg.debug('now have key for signer address {}'.format(signer_address))
signer = EIP155Signer(keystore)

rpc_id_generator = None
if args.seq:
    rpc_id_generator = IntSequenceGenerator()

auth = None
if os.environ.get('RPC_AUTHENTICATION') == 'basic':
    from chainlib.auth import BasicAuth
    auth = BasicAuth(os.environ['RPC_USERNAME'], os.environ['RPC_PASSWORD'])
conn = EthHTTPConnection(args.p, auth=auth)

send = args.s

local = args.l
if local:
    send = False

nonce_oracle = None
gas_oracle = None
if signer_address != None and not local:
    if args.nonce != None:
        nonce_oracle = OverrideNonceOracle(signer_address, args.nonce)
    else:
        nonce_oracle = RPCNonceOracle(signer_address, conn)

    if args.gas_price or args.gas_limit != None:
        gas_oracle = OverrideGasOracle(price=args.gas_price, limit=args.gas_limit, conn=conn, id_generator=rpc_id_generator)
    else:
        gas_oracle = RPCGasOracle(conn, id_generator=rpc_id_generator)

chain_spec = ChainSpec.from_chain_str(args.i)

value = args.value


g = TxFactory(chain_spec, signer=signer, gas_oracle=gas_oracle, nonce_oracle=nonce_oracle)

def main():
    recipient = None
    if args.a != None:
        recipient = add_0x(to_checksum(args.a))
        if not args.u and recipient != add_0x(recipient):
            raise ValueError('invalid checksum address')

    if local:
        j = JSONRPCRequest(id_generator=rpc_id_generator)
        o = j.template()
        o['method'] = 'eth_call'
        o['params'].append({
            'to': recipient,
            'from': signer_address,
            'value': '0x00',
            'gas': add_0x(int.to_bytes(8000000, 8, byteorder='big').hex()), # TODO: better get of network gas limit
            'gasPrice': '0x01',
            'data': add_0x(args.data),
            })
        o['params'].append('latest')
        o = j.finalize(o)
        r = conn.do(o)
        print(strip_0x(r))
        return

    elif signer_address != None:
        tx = g.template(signer_address, recipient, use_nonce=True)
        if args.data != None:
            tx = g.set_code(tx, add_0x(args.data))

        (tx_hash_hex, o) = g.finalize(tx, id_generator=rpc_id_generator)
   
        if send:
            r = conn.do(o)
            print(r)
        else:
            print(o)
            print(tx_hash_hex)

    else:
        o = raw(args.data, id_generator=rpc_id_generator)
        if send:
            r = conn.do(o)
            print(r)
        else:
            print(o)


if __name__ == '__main__':
    main()
