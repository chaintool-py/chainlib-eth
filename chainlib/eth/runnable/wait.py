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
import chainlib.eth.cli
from funga.eth.signer import EIP155Signer
from funga.eth.keystore.dict import DictKeystore
from hexathon import (
        add_0x,
        strip_0x,
        uniform as hex_uniform,
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
from chainlib.eth.error import RevertEthException
from chainlib.chain import ChainSpec
from chainlib.eth.runnable.util import decode_for_puny_humans
from chainlib.eth.jsonrpc import to_blockheight_param

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.eth.cli.argflag_std_read
argparser = chainlib.eth.cli.ArgumentParser(arg_flags)
argparser.add_argument('--ignore', type=str, action='append', default=[], help='Ignore error from the given transaction')
argparser.add_argument('--ignore-all', action='store_true', dest='ignore_all', help='Ignore errors from all transactions')
argparser.add_positional('hashes', append=True, type=str, help='Transaction hashes to wait for')
args = argparser.parse_args()
extra_args = {
    'ignore': None,
    'ignore_all': None,
    'hashes': None,
        }
config = chainlib.eth.cli.Config.from_args(args, arg_flags, extra_args=extra_args, default_config_dir=config_dir)

rpc = chainlib.eth.cli.Rpc()
conn = rpc.connect_by_config(config)

chain_spec = None
try:
    chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))
except AttributeError:
    pass


def main():

    hashes_ready = []
    hashes_ignore = []

    for hsh in config.get('_IGNORE'):
        hashes_ignore.append(add_0x(hex_uniform(strip_0x(hsh))))

    if len(config.get('_HASHES')) == 1:
        try:
            hsh = add_0x(hex_uniform(strip_0x(config.get('_HASHES')[0])))
            hashes_ready = [hsh]
        except ValueError:
            logg.debug('hash argument not a hash, will try it as a file name')
            f = open(config.get('_HASHES')[0])
            for hsh in f:
                logg.debug('hshs {}'.format(hsh))
                hashes_ready.append(add_0x(hex_uniform(strip_0x(hsh.rstrip()))))
            f.close()
    else:
        for hsh in config.get('_HASHES'):
            logg.debug('hsh {}'.format(hsh))
            hashes_ready.append(add_0x(hex_uniform(strip_0x(hsh))))
            
    for hsh in hashes_ready:
        logg.debug('processing transaction hash {}'.format(hsh))
        try:
            r = conn.wait(hsh)
        except RevertEthException:
            if config.get('_IGNORE_ALL') or hsh in hashes_ignore:
                logg.info('ignoring revert in transaction hash {}'.format(hsh))
                continue
            sys.stderr.write('revert in transaction hash {}\n'.format(hsh))
            sys.exit(1)
           

if __name__ == '__main__':
    main()


