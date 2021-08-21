# standard imports
import os

# external imports
from chainlib.cli import (
        ArgumentParser,
        argflag_std_read,
        argflag_std_write,
        argflag_std_base,
        Config as BaseConfig,
        Wallet as BaseWallet,
        Rpc as BaseRpc,
        Flag,
    )
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer

# local imports
from chainlib.eth.address import AddressChecksum
from chainlib.eth.connection import EthHTTPConnection

script_dir = os.path.dirname(os.path.realpath(__file__))

class Wallet(BaseWallet):
    """Convenience constructor to set Ethereum defaults for chainlib cli Wallet object

    :param checksummer: Address checksummer object
    :type checksummer: Implementation of chainlib.eth.address.AddressChecksum
    """
    def __init__(self, checksummer=AddressChecksum):
        super(Wallet, self).__init__(EIP155Signer, checksummer=checksummer)


class Rpc(BaseRpc):
    """Convenience constructor to set Ethereum defaults for chainlib cli Rpc object
    """
    def __init__(self, wallet=None):
        super(Rpc, self).__init__(EthHTTPConnection, wallet=wallet)


class Config(BaseConfig):
    """Convenience constructor to set Ethereum defaults for the chainlib cli config object
    """
    default_base_config_dir = os.path.join(script_dir, 'data', 'config')
    default_fee_limit = 21000
