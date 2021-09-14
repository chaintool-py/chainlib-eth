# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import sys
import os
import json
#import argparse
import logging
import select

# local imports
import chainlib.eth.cli
from chainlib.eth.address import AddressChecksum
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.tx import count
from chainlib.chain import ChainSpec
from chainlib.jsonrpc import IntSequenceGenerator
from crypto_dev_signer.keystore.dict import DictKeystore
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer
from hexathon import add_0x

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.eth.cli.argflag_std_read
argparser = chainlib.eth.cli.ArgumentParser(arg_flags)
argparser.add_positional('address', type=str, help='Ethereum address of recipient')
args = argparser.parse_args()
config = chainlib.eth.cli.Config.from_args(args, arg_flags, default_config_dir=config_dir)

holder_address = args.address
wallet = chainlib.eth.cli.Wallet()
wallet.from_config(config)
if wallet.get_signer_address() == None and holder_address != None:
    wallet.from_address(holder_address)

rpc = chainlib.eth.cli.Rpc(wallet=wallet)
conn = rpc.connect_by_config(config)


def main():
    # TODO: should tolerate if address not prefixed with 0x 
    o = count(holder_address, id_generator=rpc.id_generator)
    r = conn.do(o)
    count_result = None
    try:
        count_result = int(r, 16)
    except ValueError:
        count_result = int(r, 10)
    print(count_result)


if __name__ == '__main__':
    main()
