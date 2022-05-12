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


logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')


arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.VERBOSE | arg_flags.CHAIN_SPEC | arg_flags.RAW | arg_flags.ENV

argparser = chainlib.eth.cli.ArgumentParser()
argparser = process_args(argparser, arg, flags)
argparser.add_argument('tx_data', type=str, help='Transaction data to decode')
args = argparser.parse_args()

logg = process_log(args, logg)

config = Config()
config = process_config(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))


chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))

def main():
    decode_for_puny_humans(args.tx_data, chain_spec, sys.stdout)

if __name__ == '__main__':
    main()
