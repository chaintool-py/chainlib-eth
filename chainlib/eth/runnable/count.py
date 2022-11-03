# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import sys
import os
import json
#import argparse
import logging
import select

# external imports
from chainlib.settings import ChainSettings
from chainlib.chain import ChainSpec
from chainlib.jsonrpc import IntSequenceGenerator
from funga.eth.keystore.dict import DictKeystore
from funga.eth.signer import EIP155Signer
from hexathon import add_0x

# local imports
import chainlib.eth.cli
from chainlib.eth.cli.arg import (
        Arg,
        ArgFlag,
        process_args,
        )
from chainlib.eth.cli.config import (
        Config,
        process_config,
        )
from chainlib.eth.cli.log import process_log
from chainlib.eth.address import AddressChecksum
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.tx import count
from chainlib.eth.settings import process_settings

logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')


def process_config_local(config, arg, args, flags):
    recipient = config.get('_POSARG')
    config.add(recipient, '_RECIPIENT', False)
    return config


argparser = chainlib.eth.cli.ArgumentParser()
arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.STD_BASE_READ | arg_flags.WALLET | arg_flags.UNSAFE
argparser = process_args(argparser, arg, flags)

argparser.add_argument('address', type=str, help='Ethereum address of recipient')
args = argparser.parse_args()

logg = process_log(args, logg)
logg.debug('flags {} {} {}'.format(flags, arg_flags.SEQ, flags & arg_flags.SEQ))

config = Config()
config = process_config(config, arg, args, flags, positional_name='address')
config = process_config_local(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainSettings()
settings = process_settings(settings, config)
logg.debug('settings loaded:\n{}'.format(settings))


def main():
    # TODO: should tolerate if address not prefixed with 0x 
    o = count(
            settings.get('RECIPIENT'),
            id_generator=settings.get('RPC_ID_GENERATOR'),
            )
    r = settings.get('CONN').do(o)
    count_result = None
    try:
        count_result = int(r, 16)
    except ValueError:
        count_result = int(r, 10)
    print(count_result)


if __name__ == '__main__':
    main()
