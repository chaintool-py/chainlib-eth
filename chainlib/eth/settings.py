# standard imports
import logging

# external imports
from chainlib.settings import process_settings as base_process_settings
from chainlib.error import SignerMissingException
from hexathon import (
        add_0x,
        strip_0x,
        )
from chainlib.block import BlockSpec

# local imports
import chainlib.eth.cli
from chainlib.eth.address import to_checksum_address
from chainlib.eth.constant import ZERO_ADDRESS

logg = logging.getLogger(__name__)


def process_settings_rpc(settings, config):
    rpc = chainlib.eth.cli.Rpc(settings.get('WALLET'))
    conn = rpc.connect_by_config(config, nonce_confirmed=True)

    settings.set('CONN', conn)
    settings.set('RPC_ID_GENERATOR', rpc.id_generator)
    settings.set('RPC_SEND', config.true('_RPC_SEND'))
    settings.set('WAIT', config.true('_WAIT'))

    gas_oracle = rpc.get_gas_oracle()
    settings.set('GAS_ORACLE', gas_oracle)
    settings.set('FEE_ORACLE', gas_oracle)

    sender_address = rpc.get_sender_address()
    try:
        settings.set('SIGNER', rpc.get_signer())
    except AttributeError:
        pass
    except SignerMissingException:
        pass

    settings.set('SENDER_ADDRESS', add_0x(sender_address))

    nonce_oracle = rpc.get_nonce_oracle()
    settings.set('NONCE_ORACLE', nonce_oracle)

    return settings


def process_settings_blockspec(settings, config):
    blockspec_in = None
    try:
        blockspec_in = config.get('_HEIGHT')
    except KeyError:
        return settings

    blockspec = None
    if blockspec_in == 'latest':
        blockspec = BlockSpec.LATEST
    elif blockspec_in == 'pending':
        blockspec = BlockSpec.PENDING
    else:
        blockspec = int(blockspec_in)

    settings.set('HEIGHT', blockspec)

    return settings


def __try_zero_address(config, address):
    try:
        if int(address) == 0:
            return ZERO_ADDRESS
    except ValueError:
        pass

    try:
        if int(address, 16) == 0:
            return ZERO_ADDRESS
    except ValueError:
        pass

    recipient = to_checksum_address(address)
    if not config.true('_UNSAFE') and recipient != address:
        raise ValueError('invalid checksum address: {}'.format(address))

    return add_0x(recipient)


def __calculate_net_amount(settings, config):
    price = settings.get('FEE_PRICE')
    if price == None:
        fee_oracle = settings.get('FEE_ORACLE')
        # TODO: pass on code and input
        r = fee_oracle.get_fee()
        price = r[0]

    value = settings.get('VALUE')
    if config.true('_TOTAL'):
        delta = config.get('_FEE_LIMIT') * price
        value -= delta
        if value < 0:
            raise ValueError('Resulting value is negative')
        logg.info('total switch set, adjusting sent amount {} by {} to {}'.format(settings.get('VALUE'), delta, value))

    return value


def process_settings_wallet(settings, config):
    wallet = chainlib.eth.cli.Wallet()
    wallet.from_config(config)
    
    settings.set('WALLET', wallet)

    try:
        if config.get('_NULL'):
            settings.set('RECIPIENT', None)
            return settings
    except KeyError:
        pass

    recipient_in = None
    try:
        recipient_in = config.get('_RECIPIENT')
    except KeyError:
        return settings

    if recipient_in == None:
        return settings
    elif recipient_in == 'null':
        settings.set('RECIPIENT', None)
        return settings

    if wallet.get_signer_address() == None and recipient_in != None:
        recipient_in = wallet.from_address(recipient_in)
        recipient_in = strip_0x(recipient_in)

    recipient = __try_zero_address(config, recipient_in)

    settings.set('RECIPIENT', recipient)

    return settings


def process_settings_contract(settings, config):
    exec_address_in = None
    try:
        exec_address_in = config.get('_EXEC_ADDRESS')
    except KeyError:
        return settings

    if exec_address_in == None:
        return settings

    exec_address = to_checksum_address(exec_address_in)
    if not config.true('_UNSAFE') and exec_address != exec_address_in:
        raise ValueError('invalid checksum address: {}'.format(exec_address_in))
    exec_address = add_0x(exec_address)

    settings.set('EXEC', exec_address)
    return settings


def process_settings_data(settings, config):
    data = None
    try:
        data = config.get('_DATA')
    except KeyError:
        settings.set('DATA', None)
        return settings

    if data == None:
        return settings

    settings.set('DATA', data)
    
    return settings


def process_settings_value(settings, config):
    updated_value = __calculate_net_amount(settings, config)
    settings.set('VALUE', updated_value)

    return settings


def process_settings_hash(settings, config):
    hshs = None
    try:
        hshs = config.get('_HASH')
    except KeyError:
        return settings

    if isinstance(hshs, str):
        hshs = [hshs]

    r = []
    for hsh in hshs:
        hsh = strip_0x(hsh)
        l = len(hsh)
        if l != 64:
            raise ValueError('invalid hash length {} for {}'.format(l, hsh))
        hsh = add_0x(hsh)
        r.append(hsh)

    settings.set('HASH', r)
    
    return settings


def process_settings(settings, config):
    settings = base_process_settings(settings, config)
    settings = process_settings_wallet(settings, config)
    settings = process_settings_rpc(settings, config)
    settings = process_settings_blockspec(settings, config)
    settings = process_settings_data(settings, config)
    settings = process_settings_hash(settings, config)
    settings = process_settings_value(settings, config)
    settings = process_settings_contract(settings, config)
    return settings
