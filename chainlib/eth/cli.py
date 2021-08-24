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
from chainlib.eth.gas import (
        OverrideGasOracle,
        RPCGasOracle,
        )
from chainlib.eth.nonce import (
        OverrideNonceOracle,
        RPCNonceOracle,
        )
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

    
    def connect_by_config(self, config):
        """

        If the standard arguments for nonce and fee price/price have been defined (which generate the configuration keys "_NONCE", "_FEE_PRICE" and "_FEE_LIMIT" respectively) , the corresponding overrides for fee and nonce generators will be defined.
    
        """
        super(Rpc, self).connect_by_config(config)

        if self.can_sign():
            nonce = config.get('_NONCE')
            if nonce != None:
                self.nonce_oracle = OverrideNonceOracle(self.get_sender_address(), nonce, id_generator=self.id_generator)
            else:
                self.nonce_oracle = RPCNonceOracle(self.get_sender_address(), self.conn, id_generator=self.id_generator)

            fee_price = config.get('_FEE_PRICE')
            fee_limit = config.get('_FEE_LIMIT')
            if fee_price != None or fee_limit != None:
                self.fee_oracle = OverrideGasOracle(price=fee_price, limit=fee_limit, conn=self.conn, id_generator=self.id_generator)
            else:
                self.fee_oracle = RPCGasOracle(self.conn, id_generator=self.id_generator)

        return self.conn


    def get_gas_oracle(self):
        return self.get_fee_oracle()


class Config(BaseConfig):
    """Convenience constructor to set Ethereum defaults for the chainlib cli config object
    """
    default_base_config_dir = os.path.join(script_dir, 'data', 'config')
    default_fee_limit = 21000
