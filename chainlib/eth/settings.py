# external imports
from chainlib.settings import process_settings as base_process_settings

# local imports
import chainlib.eth.cli


def process_settings_rpc(settings, config):
    rpc = chainlib.eth.cli.Rpc()
    conn = rpc.connect_by_config(config)

    try:
        settings.set('SIGNER', rpc.get_signer())
        settings.set('SENDER_ADDRESS', rpc.get_sender_address())
    except AttributeError:
        pass

    settings.set('CONN', conn)
    settings.set('RPC_ID_GENERATOR', rpc.id_generator)
    return settings


def process_settings_wallet(settings, config):
    wallet = chainlib.eth.cli.Wallet()
    wallet.from_config(config)

    try:
        recipient = config.get('_RECIPIENT')
    except KeyError:
        return settings

    if wallet.get_signer_address() == None and recipient != None:
        recipient = wallet.from_address(recipient)

    settings.set('RECIPIENT', recipient)
    return settings


def process_settings_chain(settings, config):
    gas_oracle = rpc.get_gas_oracle()
    settings.set('GAS_ORACLE', gas_oracle)

    nonce_oracle = rpc.get_nonce_oracle()
    settings.set('NONCE_ORACLE', nonce_oracle)
    return settings 


def process_settings(settings, config):
    settings = base_process_settings(settings, config)
    settings = process_settings_wallet(settings, config)
    settings = process_settings_rpc(settings, config)
    return settings
