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
from hexathon import (
        add_0x,
        strip_0x,
        )
from chainlib.settings import ChainSettings
from chainlib.jsonrpc import (
        JSONRPCRequest,
        IntSequenceGenerator,
        )
from chainlib.chain import ChainSpec

# local imports
from chainlib.eth.address import to_checksum_address
from chainlib.eth.connection import EthHTTPConnection
from chainlib.eth.gas import Gas
from chainlib.eth.gas import balance as gas_balance
from chainlib.eth.cli.decode import decode_for_puny_humans
from chainlib.eth.address import (
        is_same_address,
        is_checksum_address,
        )
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
from chainlib.eth.settings import process_settings

logg = logging.getLogger()


def from_data_arg(data):
    try:
        data = strip_0x(data)
        logg.info('appended input hex data: {}'.format(data))
        return data
    except ValueError:
        pass

    filename = data
    try:
        f = open(filename, 'r')
    except:
        raise ValueError("data not hex and not file we can open")

    data = f.read()
    f.close()
    logg.info('appended input data from file {}: {}'.format(filename, data))

    data = data.rstrip()
    return strip_0x(data)


def process_config_local(config, arg, args, flags):
    data = ''
    if args.data != None:
        for data_arg in args.data:
            data += from_data_arg(data_arg)
    if data == '':
        data = None
    config.add(data, '_DATA', False)
    config.add(args.amount[0], '_VALUE', False)
    return config


arg_flags = ArgFlag()
arg = Arg(arg_flags)
flags = arg_flags.STD_WRITE | arg_flags.WALLET | arg_flags.VALUE | arg_flags.TAB

argparser = chainlib.eth.cli.ArgumentParser()
argparser = process_args(argparser, arg, flags)
argparser.add_argument('--data', type=str, action='append', help='Transaction data')
argparser.add_argument('amount', type=str, help='Token amount to send')
args = argparser.parse_args()

logg = process_log(args, logg)

config = Config()
config = process_config(config, arg, args, flags, positional_name='amount')
config = process_config_local(config, arg, args, flags)
logg.debug('config loaded:\n{}'.format(config))

settings = ChainSettings()
settings = process_settings(settings, config)
logg.debug('settings loaded:\n{}'.format(settings))


def balance(conn, address, id_generator):
    o = gas_balance(address, id_generator=id_generator)
    r = conn.do(o)
    try:
        balance = int(r)
    except ValueError:
        balance = strip_0x(r)
        balance = int(balance, 16)
    return balance


def main():
    g = Gas(
            settings.get('CHAIN_SPEC'),
            signer=settings.get('SIGNER'),
            gas_oracle=settings.get('FEE_ORACLE'),
            nonce_oracle=settings.get('NONCE_ORACLE'),
            )

    recipient = settings.get('RECIPIENT')

    if logg.isEnabledFor(logging.DEBUG):
        try:
            sender_balance = balance(
                    settings.get('CONN'),
                    settings.get('SENDER_ADDRESS'),
                    settings.get('RPC_ID_GENERATOR'),
                    )
            logg.debug('sender {} balance before: {}'.format(settings.get('SENDER_ADDRESS'), sender_balance))
            if settings.get('RECIPIENT') != None:
                recipient_balance = balance(
                        settings.get('CONN'),
                        settings.get('RECIPIENT'),
                        settings.get('RPC_ID_GENERATOR'),
                        )
                logg.debug('recipient {} balance before: {}'.format(settings.get('RECIPIENT'), recipient_balance))
        except urllib.error.URLError:
            pass
     
    (tx_hash_hex, o) = g.create(
            settings.get('SENDER_ADDRESS'),
            recipient,
            settings.get('VALUE'),
            data=settings.get('DATA'),
            id_generator=settings.get('RPC_ID_GENERATOR'),
        )
    
    logg.info('gas transfer from {} to {} value {} hash {}'.format(settings.get('SENDER_ADDRESS'), settings.get('RECIPIENT'), settings.get('VALUE'), tx_hash_hex))

    if settings.get('RPC_SEND'):
        settings.get('CONN').do(o)
        if config.true('_WAIT'):
            r = settings.get('CONN').wait(tx_hash_hex)
            if logg.isEnabledFor(logging.DEBUG):
                sender_balance = balance(
                        settings.get('CONN'),
                        settings.get('SENDER_ADDRESS'),
                        settings.get('RPC_ID_GENERATOR'),
                        )
                logg.debug('sender {} balance before: {}'.format(settings.get('SENDER_ADDRESS'), sender_balance))
                if settings.get('RECIPIENT') != None:
                    recipient_balance = balance(
                            settings.get('CONN'),
                            settings.get('RECIPIENT'),
                            settings.get('RPC_ID_GENERATOR'),
                            )
                    logg.debug('recipient {} balance before: {}'.format(settings.get('RECIPIENT'), recipient_balance))
            if r['status'] == 0:
                logg.critical('VM revert for {}. Wish I could tell you more'.format(tx_hash_hex))
                sys.exit(1)
        print(tx_hash_hex)
    else:
        if config.true('_RAW'):
            print(o['params'][0])
        else:
            io_str = io.StringIO()
            decode_for_puny_humans(
                    o['params'][0],
                    settings.get('CHAIN_SPEC'),
                    io_str,
                    fields=config.get('_OUTARG'),
                    skip_keys=config.true('_RAW'),
                    )
            sys.stdout.write(io_str.getvalue())
 


if __name__ == '__main__':
    main()
