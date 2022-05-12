# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import sys
import os
import json
import argparse
import logging
import select

# external imports
import chainlib.eth.cli
from chainlib.eth.tx import unpack
from chainlib.settings import ChainSettings
from chainlib.chain import ChainSpec

# local imports
import chainlib.eth.cli
from chainlib.eth.runnable.util import decode_for_puny_humans
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
from chainlib.eth.settings import process_settings


logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')


def process_config_local(config, arg, args, flags):
    config.add(args.tx_data, '_TX_DATA', False)
    return config


arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.VERBOSE | arg_flags.CHAIN_SPEC | arg_flags.RAW | arg_flags.ENV | arg_flags.SEQ

argparser = chainlib.eth.cli.ArgumentParser()
argparser = process_args(argparser, arg, flags)
argparser.add_argument('tx_data', type=str, help='Transaction data to decode')
args = argparser.parse_args()

logg = process_log(args, logg)

config = Config()
config = process_config(config, arg, args, flags)
config = process_config_local(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainSettings()
settings = process_settings(settings, config)
logg.debug('settings loaded:\n{}'.format(settings))


def main():
    decode_for_puny_humans(
            config.get('_TX_DATA'),
            settings.get('CHAIN_SPEC'),
            sys.stdout,
            )

if __name__ == '__main__':
    main()
