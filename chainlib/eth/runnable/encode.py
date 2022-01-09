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
import chainlib.eth.cli
from chainlib.eth.cli.encode import CLIEncoder
from funga.eth.signer import EIP155Signer
from funga.eth.keystore.dict import DictKeystore
from hexathon import (
        add_0x,
        strip_0x,
        )

# local imports
from chainlib.eth.constant import ZERO_ADDRESS
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
        TxFormat,
        raw,
        )
from chainlib.error import SignerMissingException
from chainlib.chain import ChainSpec
from chainlib.eth.runnable.util import decode_for_puny_humans
from chainlib.eth.jsonrpc import to_blockheight_param
from chainlib.eth.address import to_checksum_address

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.eth.cli.argflag_std_write | chainlib.eth.cli.Flag.EXEC | chainlib.eth.cli.Flag.FEE
argparser = chainlib.eth.cli.ArgumentParser(arg_flags)
argparser.add_argument('--notx', action='store_true', help='Network send is not a transaction')
argparser.add_argument('--signature', type=str, help='Method signature to encode')
argparser.add_argument('contract_args', type=str, nargs='*', help='arguments to encode')
args = argparser.parse_args()
extra_args = {
    'signature': None,
    'contract_args': None,
    'notx': None,
        }
config = chainlib.eth.cli.Config.from_args(args, arg_flags, extra_args=extra_args, default_config_dir=config_dir)

block_all = args.ww
block_last = args.w or block_all

wallet = chainlib.eth.cli.Wallet(EIP155Signer)
wallet.from_config(config)

rpc = chainlib.eth.cli.Rpc(wallet=wallet)
conn = rpc.connect_by_config(config)

send = config.true('_RPC_SEND')

chain_spec = None
try:
    chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))
except AttributeError:
    pass


def main():

    signer_address = ZERO_ADDRESS
    signer = None
    try:
        signer = rpc.get_signer()
        signer_address = rpc.get_signer_address()
    except SignerMissingException:
        pass

    code = '0x'
    cli_encoder = CLIEncoder(signature=config.get('_SIGNATURE'))

    for arg in config.get('_CONTRACT_ARGS'):
        cli_encoder.add_from(arg)
    
    code += cli_encoder.get()

    if not config.get('_SIGNATURE'):
        print(strip_0x(code))
        return

    exec_address = config.get('_EXEC_ADDRESS')
    if exec_address:
        exec_address = add_0x(to_checksum_address(exec_address))

    if signer == None or config.true('_NOTX'):
        if config.true('_RAW'):
            print(strip_0x(code))
            return

        if not exec_address:
            argparser.error('exec address (-e) must be defined')

        c = TxFactory(chain_spec)
        j = JSONRPCRequest(id_generator=rpc.id_generator)
        o = j.template()
        o['method'] = 'eth_call'
        gas_limit = add_0x(int.to_bytes(config.get('_FEE_LIMIT'), 8, byteorder='big').hex(), compact_value=True)
        gas_price = add_0x(int.to_bytes(config.get('_FEE_PRICE'), 8, byteorder='big').hex(), compact_value=True)
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
        r = conn.do(o)
        try:
            print(strip_0x(r))
            return
        except ValueError:
            sys.stderr.write('query returned an empty value ({})\n'.format(r))
            sys.exit(1)

    if not exec_address:
        argparser.error('exec address (-e) must be defined')

    if chain_spec == None:
        raise ValueError('chain spec must be specified')

    c = TxFactory(chain_spec, signer=signer, gas_oracle=rpc.get_gas_oracle(), nonce_oracle=rpc.get_nonce_oracle())
    tx = c.template(signer_address, config.get('_EXEC_ADDRESS'), use_nonce=True)
    tx = c.set_code(tx, code)
    tx_format = TxFormat.JSONRPC
    if config.get('_RAW'):
        tx_format = TxFormat.RLP_SIGNED
    (tx_hash_hex, o) = c.finalize(tx, tx_format=tx_format)
    if send:
        r = conn.do(o)
        print(r)
    else:
        if config.get('_RAW'):
            o = strip_0x(o)
        print(o)

if __name__ == '__main__':
    main()
