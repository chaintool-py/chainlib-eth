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
from hexathon import (
        add_0x,
        strip_0x,
        )
from chainlib.error import SignerMissingException
from chainlib.chain import ChainSpec

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
    config.add(args.deploy, '_DEPLOY', False)
    config.add(args.mode, '_MODE', False)
    data = config.get('_POSARG')

    try:
        data = strip_0x(data)
    except TypeError:
        data = stdin_arg()
        data = strip_0x(data)

    config.add(data, '_DATA', False)

    return config


arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.STD_WRITE | arg_flags.EXEC

argparser = chainlib.eth.cli.ArgumentParser()
argparser = process_args(argparser, arg, flags)
argparser.add_argument('--deploy', action='store_true', help='Deploy data as contract')
argparser.add_argument('--mode', choices=['tx', 'call'], type=str, help='Mode of operation')
argparser.add_argument('data', type=str, help='Transaction data')
args = argparser.parse_args()

logg = process_log(args, logg)

config = Config()
config = process_config(config, arg, args, flags, positional_name='data')
config = process_config_local(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainSettings()
settings = process_settings(settings, config)
logg.debug('settings loaded:\n{}'.format(settings))


def main():
    if config.get('_EXEC_ADDRESS') != None or config.true('_DEPLOY'):
        if not args.u and exec_address != exec_address:
            raise ValueError('invalid checksum address')

        if settings.get('SENDER_ADDRESS'):
            j = JSONRPCRequest(id_generator=settings.get('RPC_ID_GENERATOR'))
            o = j.template()
            o['method'] = 'eth_call'
            o['params'].append({
                'to': settings.get('EXEC'),
                'from': settings.get('SENDER_ADDRESS'),
                'value': '0x00',
                'gas': add_0x(int.to_bytes(8000000, 8, byteorder='big').hex()), # TODO: better get of network gas limit
                'gasPrice': '0x01',
                'data': add_0x(config.get('_DATA')),
                })
            height = to_blockheight_param(config.get('_HEIGHT'))
            o['params'].append(height)
            o = j.finalize(o)
            r = settings.get('CONN').do(o)
            try:
                print(strip_0x(r))
            except ValueError:
                sys.stderr.write('query returned an empty value ({})\n'.format(r))
                sys.exit(1)

        else:
            if settings.get('CHAIN_SPEC') == None:
                raise ValueError('chain spec must be specified')
            g = TxFactory(
                    settings.get('CHAIN_SPEC'),
                    signer=settings.get('SIGNER'),
                    gas_oracle=settings.get('GAS_ORACLE'),
                    nonce_oracle=settings.get('NONCE_ORACLE'),
                )
            tx = g.template(
                    settings.get('SENDER_ADDRESS'),
                    settings.get('EXEC'),
                    use_nonce=True,
                    )
            if config.get('_DATA') != None:
                tx = g.set_code(tx, add_0x(config.get('_DATA')))

            (tx_hash_hex, o) = g.finalize(tx, id_generator=rpc.id_generator)
       
            if send:
                r = settings.get('CONN').do(o)
                print(r)
            else:
                if config.get('_RAW'):
                    o = strip_0x(o)
                print(o)

    else:
        o = raw(config.get('_DATA'), id_generator=settings.get('RPC_ID_GENERATOR'))
        if settings.get('RPC_SEND'):
            tx_hash_hex = settings.get('CONN').do(o)
            out = tx_hash_hex
            if config.true('_WAIT'):
                #r = settings.get('CONN').wait(tx_hash_hex)
                r = settings.get('CONN').wait(tx_hash_hex)
                if r['status'] == 0:
                    logg.critical('VM revert for {}. Wish I could tell you more'.format(tx_hash_hex))
                    sys.exit(1)
                if config.true('_RAW'):
                    out = json.dumps(r)
            sys.stdout.write(out)
            if not config.true('_NULL'):
                sys.stdout.write('\n')

        else:
            print(o)


if __name__ == '__main__':
    main()
