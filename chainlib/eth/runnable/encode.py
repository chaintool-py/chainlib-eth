# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import io
import sys
import os
import json
import argparse
import logging
import urllib
import sha3

# external imports
#from chainlib.cli import flag_reset
from chainlib.settings import ChainSettings
from funga.eth.signer import EIP155Signer
from funga.eth.keystore.dict import DictKeystore
from hexathon import (
        add_0x,
        strip_0x,
        )

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
from chainlib.eth.cli.encode import CLIEncoder
from chainlib.eth.constant import ZERO_ADDRESS
from chainlib.eth.address import to_checksum
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.settings import process_settings
from chainlib.jsonrpc import (
        JSONRPCRequest,
        IntSequenceGenerator,
        )
from chainlib.eth.tx import (
        TxFactory,
        TxFormat,
        raw,
        )
from chainlib.error import SignerMissingException
from chainlib.chain import ChainSpec
from chainlib.eth.jsonrpc import to_blockheight_param
from chainlib.eth.address import to_checksum_address

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')


def process_config_local(config, arg, args, flags):
    config.add(args.signature, '_SIGNATURE', False)
    config.add(args.contract_args, '_CONTRACT_ARGS', False)
    # workaround to avoid rpc lookup of fee parameters when using arg mode
    if args.mode == 'arg':
        config.add(0, '_FEE_PRICE', True)
        config.add(0, '_FEE_LIMIT', True)
    return config

arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.STD_WRITE | arg_flags.EXEC | arg_flags.FEE | arg_flags.FMT_HUMAN | arg_flags.FMT_WIRE | arg_flags.FMT_RPC

argparser = chainlib.eth.cli.ArgumentParser()
argparser = process_args(argparser, arg, flags)
argparser.add_argument('--mode', type=str, choices=['tx', 'call', 'arg'], help='Mode of operation')
argparser.add_argument('--signature', type=str, help='Method signature to encode')
argparser.add_argument('contract_args', type=str, nargs='*', help='arguments to encode')
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

    signer_address = ZERO_ADDRESS
    signer = None
    conn = settings.get('CONN')
    signer_address = settings.get('SENDER_ADDRESS')

    code = '0x'
    cli_encoder = CLIEncoder(signature=config.get('_SIGNATURE'))

    for arg in config.get('_CONTRACT_ARGS'):
        cli_encoder.add_from(arg)
    
    code += cli_encoder.get()

    exec_address = config.get('_EXEC_ADDRESS')
    if exec_address:
        exec_address = add_0x(to_checksum_address(exec_address))

    mode = args.mode
    if mode == None:
        if signer == None:
            mode = 'call'
        else:
            mode = 'tx'

    if not config.get('_SIGNATURE'):
        if mode != 'arg':
            logg.error('mode tx without contract method signature makes no sense. Use eth-get with --data instead.')
            sys.exit(1)

    if mode == 'arg':
        print(strip_0x(code))
        return
    elif not exec_address:
        logg.error('exec address (-e) must be defined with mode "{}"'.format(args.mode))
        sys.exit(1)

    if config.get('RPC_PROVIDER'):
        logg.debug('provider {}'.format(config.get('RPC_PROVIDER')))
        if not config.get('_FEE_LIMIT') or not config.get('_FEE_PRICE'):
            #gas_oracle = rpc.get_gas_oracle()
            gas_oracle = settings.get('GAS_ORACLE')
            (price, limit) = gas_oracle.get_gas()
        if not config.get('_FEE_PRICE'):
            config.add(price, '_FEE_PRICE')
        if not config.get('_FEE_LIMIT'):
            config.add(limit, '_FEE_LIMIT')

        if mode == 'tx':
            if not config.get('_NONCE'):
                nonce_oracle = settings.get('NONCE_ORACLE') #rpc.get_nonce_oracle()
                config.add(nonce_oracle.get_nonce(), '_NONCE')
    else: 
        for arg in [
                '_FEE_PRICE',
                '_FEE_LIMIT',
                '_NONCE',
                ]:
            if not config.get(arg):
                logg.error('--{} must be specified when no rpc provider has been set.'.format(arg.replace('_', '-').lower()))
                sys.exit(1)


    if mode == 'call': #signer == None or config.true('_NOTX'):
        c = TxFactory(settings.get('CHAIN_SPEC'))
        j = JSONRPCRequest(id_generator=settings.get('RPC_ID_GENERATOR'))
        o = j.template()
        gas_limit = add_0x(int.to_bytes(config.get('_FEE_LIMIT'), 8, byteorder='big').hex(), compact_value=True)
        gas_price = add_0x(int.to_bytes(config.get('_FEE_PRICE'), 8, byteorder='big').hex(), compact_value=True)
        o['method'] = 'eth_call'
        o['params'].append({
                'to': exec_address,
                'from': signer_address,
                'value': '0x0',
                'gas': gas_limit, # TODO: better get of network gas limit
                'gasPrice': gas_price,
                'data': add_0x(code),
                })
        height = to_blockheight_param(config.get('_HEIGHT'))
        o['params'].append(height)
        o = j.finalize(o)

        if settings.get('RPC_SEND'):
            r = conn.do(o)
            try:
                print(strip_0x(r))
                return
            except ValueError:
                sys.stderr.write('query returned an empty value ({})\n'.format(r))
                sys.exit(1)
        else:
            print(o)
            return

    if settings.get('SIGNER') == None:
        logg.error('mode "tx" without signer does not make sense. Please specify a key file with -y.')
        sys.exit(1)

    if settings.get('CHAIN_SPEC') == None:
        raise ValueError('chain spec must be specified')

    c = TxFactory(
            settings.get('CHAIN_SPEC'),
            signer=settings.get('SIGNER'),
            gas_oracle=settings.get('FEE_ORACLE'),
            nonce_oracle=settings.get('NONCE_ORACLE'),
            )

    tx = c.template(
            settings.get('SENDER_ADDRESS'),
            settings.get('EXEC'),
            use_nonce=True,
            )
    tx = c.set_code(tx, code)
    tx_format = TxFormat.JSONRPC
    if config.get('_RAW'):
        tx_format = TxFormat.RLP_SIGNED
    (tx_hash_hex, o) = c.finalize(tx, tx_format=tx_format)
    if settings.get('RPC_SEND'):
        r = conn.do(o)
        if settings.get('WAIT'):
            r = conn.wait(tx_hash_hex)
            if r['status'] == 0:
                logg.critical('VM revert. Wish I could tell you more')
                sys.exit(1)
        print(tx_hash_hex)
    else:
        if config.get('_RAW'):
            o = strip_0x(o)
        print(o)

if __name__ == '__main__':
    main()
