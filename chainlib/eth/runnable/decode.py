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
from chainlib.eth.runnable.util import decode_for_puny_humans

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.eth.cli.Flag.VERBOSE | chainlib.eth.cli.Flag.CHAIN_SPEC | chainlib.eth.cli.Flag.ENV_PREFIX | chainlib.eth.cli.Flag.RAW
argparser = chainlib.eth.cli.ArgumentParser(arg_flags)
argparser.add_positional('tx_data', type=str, help='Transaction data to decode')
args = argparser.parse_args()
config = chainlib.eth.cli.Config.from_args(args, arg_flags, default_config_dir=config_dir)

chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))

def main():
    decode_for_puny_humans(args.tx_data, chain_spec, sys.stdout)

if __name__ == '__main__':
    main()
