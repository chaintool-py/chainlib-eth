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
from funga.eth.signer import EIP155Signer

logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 

argparser = chainlib.eth.cli.ArgumentParser()
arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.STD_READ
argparser = process_args(argparser, arg, flags)

argparser.add_argument('address', type=str, help='Ethereum address of recipient')
args = argparser.parse_args()

logg = process_log(args, logg)
logg.debug('flags {} {} {}'.format(flags, arg_flags.SEQ, flags & arg_flags.SEQ))

config = Config()
config = process_config(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))

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
