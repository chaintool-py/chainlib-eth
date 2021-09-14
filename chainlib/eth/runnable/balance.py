# SPDX-License-Identifier: GPL-3.0-or-later

# standard imports
import os
import logging

# external imports
from hexathon import (
        add_0x,
        strip_0x,
        even,
        )

# local imports
import chainlib.eth.cli
from chainlib.eth.address import AddressChecksum
from chainlib.jsonrpc import (
        jsonrpc_result,
        IntSequenceGenerator,
        )
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.gas import (
        OverrideGasOracle,
        balance,
        )
from chainlib.chain import ChainSpec
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer

logging.basicConfig(level=logging.WARNING)
logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 
#config_dir = os.path.join(script_dir, '..', 'data', 'config')

arg_flags = chainlib.eth.cli.argflag_std_read
argparser = chainlib.eth.cli.ArgumentParser(arg_flags)
argparser.add_positional('address', type=str, help='Ethereum address of recipient')
args = argparser.parse_args()
config = chainlib.eth.cli.Config.from_args(args, arg_flags)

wallet = chainlib.eth.cli.Wallet()
wallet.from_config(config)
holder_address = args.address
if wallet.get_signer_address() == None and holder_address != None:
    holder_address = wallet.from_address(holder_address)

rpc = chainlib.eth.cli.Rpc()
conn = rpc.connect_by_config(config)

chain_spec = ChainSpec.from_chain_str(config.get('CHAIN_SPEC'))

def main():
    r = None
    decimals = 18

    o = balance(holder_address, id_generator=rpc.id_generator)
    r = conn.do(o)
   
    hx = strip_0x(r)
    balance_value = int(hx, 16)
    logg.debug('balance {} = {} decimals {}'.format(even(hx), balance_value, decimals))

    balance_str = str(balance_value)
    balance_len = len(balance_str)
    if balance_len < decimals + 1:
        print('0.{}'.format(balance_str.zfill(decimals)))
    else:
        offset = balance_len-decimals
        print('{}.{}'.format(balance_str[:offset],balance_str[offset:]))


if __name__ == '__main__':
    main()
