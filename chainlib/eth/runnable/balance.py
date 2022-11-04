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
from chainlib.settings import ChainSettings
from chainlib.chain import ChainSpec
from funga.eth.signer import EIP155Signer
from chainlib.jsonrpc import (
        jsonrpc_result,
        IntSequenceGenerator,
        )

# local imports
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
from chainlib.eth.address import AddressChecksum
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.gas import (
        OverrideGasOracle,
        balance,
        )
from chainlib.eth.settings import process_settings
from chainlib.eth.jsonrpc import to_blockheight_param


logg = logging.getLogger()

script_dir = os.path.dirname(os.path.realpath(__file__)) 


def process_config_local(config, arg, args, flags):
    recipient = None
    address = config.get('_POSARG')
    if address:
        recipient = add_0x(address)
    else:
        recipient = stdin_arg()
    config.add(recipient, '_RECIPIENT', False)
    return config


arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.STD_READ

argparser = chainlib.eth.cli.ArgumentParser()
argparser = process_args(argparser, arg, flags)
argparser.add_argument('address', type=str, help='Ethereum address of recipient')

args = argparser.parse_args()

logg = process_log(args, logg)
logg.debug('flags {} {} {}'.format(flags, arg_flags.SEQ, flags & arg_flags.SEQ))

config = Config()
config = process_config(config, arg, args, flags, positional_name='address')
config = process_config_local(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainSettings()
settings = process_settings(settings, config)


def main():
    r = None
    decimals = 18

    height = to_blockheight_param(config.get('_HEIGHT'))
    o = balance(settings.get('RECIPIENT'), id_generator=settings.get('RPC_ID_GENERATOR'), height=height)
    r = settings.get('CONN').do(o)
   
    hx = strip_0x(r)
    balance_value = int(hx, 16)
    logg.debug('balance {} = {} decimals {}'.format(even(hx), balance_value, decimals))

    balance_str = str(balance_value)
    balance_len = len(balance_str)
    if config.get('_RAW'):
        print(balance_str)
    else:
        if balance_len < decimals + 1:
            print('0.{}'.format(balance_str.zfill(decimals)))
        else:
            offset = balance_len-decimals
            print('{}.{}'.format(balance_str[:offset],balance_str[offset:]))


if __name__ == '__main__':
    main()
