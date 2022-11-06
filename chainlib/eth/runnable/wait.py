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
from chainlib.settings import ChainSettings
from funga.eth.signer import EIP155Signer
from funga.eth.keystore.dict import DictKeystore
from chainlib.chain import ChainSpec
from chainlib.jsonrpc import (
        JSONRPCRequest,
        IntSequenceGenerator,
        )
from hexathon import (
        add_0x,
        strip_0x,
        uniform as hex_uniform,
        )

# local imports
from chainlib.eth.address import to_checksum
from chainlib.eth.connection import EthHTTPConnection
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
from chainlib.eth.error import RevertEthException
from chainlib.eth.jsonrpc import to_blockheight_param
import chainlib.eth.cli
from chainlib.eth.cli.arg import (
        Arg,
        ArgFlag,
        process_args,
        stdin_arg,
        )
from chainlib.eth.cli.config import (
        Config,
        process_config,
        )
from chainlib.eth.cli.log import process_log
from chainlib.eth.settings import process_settings

logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')


def process_config_local(config, arg, args, flags):
    config.add(args.ignore, '_IGNORE', False)
    config.add(args.ignore_all, '_IGNORE_ALL', False)

    hsh = config.get('_POSARG')
    try:
        hsh = strip_0x(hsh)
    except TypeError:
        hsh = stdin_arg()
        hsh = strip_0x(hsh)

    config.add(hsh, '_HASH', False)

    return config


def process_settings_local(settings, config):
    settings.set('HASH', config.get('_HASH'))
    return settings


arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.STD_READ

argparser = chainlib.eth.cli.ArgumentParser()
argparser = process_args(argparser, arg, flags)
argparser.add_argument('--ignore', type=str, action='append', default=[], help='Ignore error from the given transaction')
argparser.add_argument('--ignore-all', action='store_true', dest='ignore_all', help='Ignore errors from all transactions')
argparser.add_argument('hashes', nargs='*', type=str, help='Transaction hashes to wait for')
args = argparser.parse_args()

logg = process_log(args, logg)

config = Config()
config = process_config(config, arg, args, flags, positional_name='hashes')
config = process_config_local(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainSettings()
settings = process_settings(settings, config)
logg.debug('settings loaded:\n{}'.format(settings))


def main():

    hashes_ready = []
    hashes_ignore = []

    for hsh in config.get('_IGNORE'):
        hashes_ignore.append(add_0x(hex_uniform(strip_0x(hsh))))

    if len(settings.get('HASH')) == 1:
        hsh = settings.get('HASH')[0]
        try:
            hashes_ready = [hsh]
        except ValueError:
            logg.debug('hash argument not a hash, will try it as a file name')
            f = open(hsh)
            for hsh in f:
                hashes_ready.append(hsh)
            f.close()
    else:
        for hsh in settings.get('HASH'):
            if hsh in hashes_ready:
                logg.debug('skipping duplicate hash {}'.format(hsh))
                continue
            hashes_ready.append(hsh)
            
    for hsh in hashes_ready:
        logg.info('processing transaction hash {}'.format(hsh))
        try:
            r = settings.get('CONN').wait(hsh)
        except RevertEthException:
            if config.get('_IGNORE_ALL') or hsh in hashes_ignore:
                logg.debug('ignoring revert in transaction hash {}'.format(hsh))
                continue
            sys.stderr.write('revert in transaction hash {}\n'.format(hsh))
            sys.exit(1)
           

if __name__ == '__main__':
    main()
