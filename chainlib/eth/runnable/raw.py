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
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer
from crypto_dev_signer.keystore.dict import DictKeystore
from hexathon import (
        add_0x,
        strip_0x,
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
from chainlib.error import SignerMissingException
from chainlib.chain import ChainSpec
from chainlib.eth.runnable.util import decode_for_puny_humans
from chainlib.eth.jsonrpc import to_blockheight_param

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.eth.cli.argflag_std_write | chainlib.eth.cli.Flag.EXEC
argparser = chainlib.eth.cli.ArgumentParser(arg_flags)
argparser.add_positional('data', type=str, help='Transaction data')
args = argparser.parse_args()
config = chainlib.eth.cli.Config.from_args(args, arg_flags, default_config_dir=config_dir)

block_all = args.ww
block_last = args.w or block_all

wallet = chainlib.eth.cli.Wallet(EIP155Signer)
wallet.from_config(config)

rpc = chainlib.eth.cli.Rpc(wallet=wallet)
conn = rpc.connect_by_config(config)

send = config.true('_RPC_SEND')

if config.get('_EXEC_ADDRESS') != None:
    send = False

chain_spec = None
try:
    chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))
except AttributeError:
    pass

def main():

    signer_address = None
    try:
        signer = rpc.get_signer()
        signer_address = rpc.get_signer_address()
    except SignerMissingException:
        pass

    if config.get('_EXEC_ADDRESS') != None:
        exec_address = add_0x(to_checksum(config.get('_EXEC_ADDRESS')))
        if not args.u and exec_address != add_0x(exec_address):
            raise ValueError('invalid checksum address')

        j = JSONRPCRequest(id_generator=rpc.id_generator)
        o = j.template()
        o['method'] = 'eth_call'
        o['params'].append({
            'to': exec_address,
            'from': signer_address,
            'value': '0x00',
            'gas': add_0x(int.to_bytes(8000000, 8, byteorder='big').hex()), # TODO: better get of network gas limit
            'gasPrice': '0x01',
            'data': add_0x(args.data),
            })
        height = to_blockheight_param(config.get('_HEIGHT'))
        o['params'].append(height)
        o = j.finalize(o)
        r = conn.do(o)
        try:
            print(strip_0x(r))
        except ValueError:
            sys.stderr.write('query returned an empty value\n')
            sys.exit(1)
        return

        if signer_address != None:
            if chain_spec == None:
                raise ValueError('chain spec must be specified')
            g = TxFactory(chain_spec, signer=rpc.get_signer(), gas_oracle=rpc.get_gas_oracle(), nonce_oracle=rpc.get_nonce_oracle())
            tx = g.template(signer_address, exec_address, use_nonce=True)
            if args.data != None:
                tx = g.set_code(tx, add_0x(args.data))

            (tx_hash_hex, o) = g.finalize(tx, id_generator=rpc.id_generator)
       
            if send:
                r = conn.do(o)
                print(r)
            else:
                print(o)
                print(tx_hash_hex)

    else:
        o = raw(args.data, id_generator=rpc.id_generator)
        if send:
            r = conn.do(o)
            print(r)
        else:
            print(o)


if __name__ == '__main__':
    main()
