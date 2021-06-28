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
        Gas,
        )
from chainlib.eth.gas import balance as gas_balance
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
argparser.add_argument('--env-prefix', default=os.environ.get('CONFINI_ENV_PREFIX'), dest='env_prefix', type=str, help='environment prefix for variables to overwrite configuration')
argparser.add_argument('--nonce', type=int, help='override nonce')
argparser.add_argument('--gas-price', dest='gas_price', type=int, help='override gas price')
argparser.add_argument('--gas-limit', dest='gas_limit', type=int, help='override gas limit')
argparser.add_argument('-u', '--unsafe', dest='u', action='store_true', help='Auto-convert address to checksum adddress')
argparser.add_argument('--seq', action='store_true', help='Use sequential rpc ids')
argparser.add_argument('-v', action='store_true', help='Be verbose')
argparser.add_argument('-vv', action='store_true', help='Be more verbose')
argparser.add_argument('-s', '--send', dest='s', action='store_true', help='Send to network')
argparser.add_argument('recipient', type=str, help='ethereum address of recipient')
argparser.add_argument('amount', type=int, help='gas value in wei')
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

nonce_oracle = None
if args.nonce != None:
    nonce_oracle = OverrideNonceOracle(signer_address, args.nonce, id_generator=rpc_id_generator)
else:
    nonce_oracle = RPCNonceOracle(signer_address, conn, id_generator=rpc_id_generator)

gas_oracle = None
if args.gas_price or args.gas_limit != None:
    gas_oracle = OverrideGasOracle(price=args.gas_price, limit=args.gas_limit, conn=conn, id_generator=rpc_id_generator)
else:
    gas_oracle = RPCGasOracle(conn, id_generator=rpc_id_generator)


chain_spec = ChainSpec.from_chain_str(args.i)

value = args.amount

send = args.s

g = Gas(chain_spec, signer=signer, gas_oracle=gas_oracle, nonce_oracle=nonce_oracle)


def balance(address, id_generator):
    o = gas_balance(address, id_generator=id_generator)
    r = conn.do(o)
    hx = strip_0x(r)
    return int(hx, 16)


def main():
    recipient = to_checksum(args.recipient)
    if not args.u and recipient != add_0x(args.recipient):
        raise ValueError('invalid checksum address')

    logg.info('gas transfer from {} to {} value {}'.format(signer_address, recipient, value))
    if logg.isEnabledFor(logging.DEBUG):
        try:
            sender_balance = balance(signer_address, rpc_id_generator)
            recipient_balance = balance(recipient, rpc_id_generator)
            logg.debug('sender {} balance before: {}'.format(signer_address, sender_balance))
            logg.debug('recipient {} balance before: {}'.format(recipient, recipient_balance))
        except urllib.error.URLError:
            pass
     
    (tx_hash_hex, o) = g.create(signer_address, recipient, value, id_generator=rpc_id_generator)

    if send:
        conn.do(o)
        if block_last:
            r = conn.wait(tx_hash_hex)
            if logg.isEnabledFor(logging.DEBUG):
                sender_balance = balance(signer_address, rpc_id_generator)
                recipient_balance = balance(recipient, rpc_id_generator)
                logg.debug('sender {} balance after: {}'.format(signer_address, sender_balance))
                logg.debug('recipient {} balance after: {}'.format(recipient, recipient_balance))
            if r['status'] == 0:
                logg.critical('VM revert. Wish I could tell you more')
                sys.exit(1)
        print(tx_hash_hex)
    else:
        if logg.isEnabledFor(logging.INFO):
            io_str = io.StringIO()
            decode_for_puny_humans(o['params'][0], chain_spec, io_str)
            print(io_str.getvalue())
        else:
            print(o['params'][0])
 


if __name__ == '__main__':
    main()
