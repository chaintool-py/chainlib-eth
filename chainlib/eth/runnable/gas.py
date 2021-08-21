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
from hexathon import (
        add_0x,
        strip_0x,
        )

# local imports
from chainlib.eth.address import to_checksum_address
from chainlib.eth.connection import EthHTTPConnection
from chainlib.jsonrpc import (
        JSONRPCRequest,
        IntSequenceGenerator,
        )
from chainlib.eth.gas import Gas
from chainlib.eth.gas import balance as gas_balance
from chainlib.chain import ChainSpec
from chainlib.eth.runnable.util import decode_for_puny_humans
import chainlib.eth.cli

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

arg_flags = chainlib.eth.cli.argflag_std_write | chainlib.eth.cli.Flag.WALLET
argparser = chainlib.eth.cli.ArgumentParser(arg_flags)
argparser.add_argument('--data', type=str, help='Transaction data')
argparser.add_positional('amount', type=int, help='Token amount to send')
args = argparser.parse_args()
extra_args = {
    'data': None,
    'amount': None,
        }
#config = chainlib.eth.cli.Config.from_args(args, arg_flags, extra_args=extra_args, default_config_dir=config_dir)
config = chainlib.eth.cli.Config.from_args(args, arg_flags, extra_args=extra_args)

block_all = args.ww
block_last = args.w or block_all

wallet = chainlib.eth.cli.Wallet()
wallet.from_config(config)

rpc = chainlib.eth.cli.Rpc(wallet=wallet)
conn = rpc.connect_by_config(config)

chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))

value = config.get('_AMOUNT')

send = config.true('_RPC_SEND')


def balance(address, id_generator):
    o = gas_balance(address, id_generator=id_generator)
    r = conn.do(o)
    hx = strip_0x(r)
    return int(hx, 16)


def main():
    signer = rpc.get_signer()
    signer_address = rpc.get_sender_address()

    g = Gas(chain_spec, signer=signer, gas_oracle=rpc.get_gas_oracle(), nonce_oracle=rpc.get_nonce_oracle())

    recipient = to_checksum_address(config.get('_RECIPIENT'))
    if not config.true('_UNSAFE') and recipient != add_0x(config.get('_RECIPIENT')):
        raise ValueError('invalid checksum address')

    logg.info('gas transfer from {} to {} value {}'.format(signer_address, recipient, value))
    if logg.isEnabledFor(logging.DEBUG):
        try:
            sender_balance = balance(signer_address, rpc.id_generator)
            recipient_balance = balance(recipient, rpc.id_generator)
            logg.debug('sender {} balance before: {}'.format(signer_address, sender_balance))
            logg.debug('recipient {} balance before: {}'.format(recipient, recipient_balance))
        except urllib.error.URLError:
            pass
     
    (tx_hash_hex, o) = g.create(signer_address, recipient, value, data=config.get('_DATA'), id_generator=rpc.id_generator)

    if send:
        conn.do(o)
        if block_last:
            r = conn.wait(tx_hash_hex)
            if logg.isEnabledFor(logging.DEBUG):
                sender_balance = balance(signer_address, rpc.id_generator)
                recipient_balance = balance(recipient, rpc.id_generator)
                logg.debug('sender {} balance after: {}'.format(signer_address, sender_balance))
                logg.debug('recipient {} balance after: {}'.format(recipient, recipient_balance))
            if r['status'] == 0:
                logg.critical('VM revert. Wish I could tell you more')
                sys.exit(1)
        print(tx_hash_hex)
    else:
        #if logg.isEnabledFor(logging.INFO):
        if config.true('_RAW'):
            print(o['params'][0])
        else:
            io_str = io.StringIO()
            decode_for_puny_humans(o['params'][0], chain_spec, io_str)
            print(io_str.getvalue())
 


if __name__ == '__main__':
    main()
