# standard imports
import os
import logging

# external imports
from chainlib.cli import (
        ArgumentParser,
        argflag_std_read,
        argflag_std_write,
        argflag_std_base,
        Config as BaseConfig,
        Wallet as BaseWallet,
        Rpc as BaseRpc, Flag,
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

logg = logging.getLogger(__name__)

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
            nonce = None
            try:
                nonce = config.get('_NONCE')
            except KeyError:
                pass
            if nonce != None:
                self.nonce_oracle = OverrideNonceOracle(self.get_sender_address(), nonce, id_generator=self.id_generator)
            else:
                self.nonce_oracle = RPCNonceOracle(self.get_sender_address(), self.conn, id_generator=self.id_generator)
        
        fee_price = None
        fee_limit = None
        try:
            fee_price = config.get('_FEE_PRICE')
        except KeyError:
            pass

        try:
            fee_limit = config.get('_FEE_LIMIT')
        except KeyError:
            pass

        if fee_price != None or fee_limit != None:
            self.fee_oracle = OverrideGasOracle(price=fee_price, limit=fee_limit, conn=self.conn, id_generator=self.id_generator)
        else:
            self.fee_oracle = RPCGasOracle(self.conn, id_generator=self.id_generator)

        error_parser = None
        if config.get('RPC_DIALECT') == 'openethereum':
            from chainlib.eth.dialect.openethereum import DialectErrorParser
            self.error_parser = DialectErrorParser()

        return self.conn


    def get_gas_oracle(self):
        return self.get_fee_oracle()


class Config(BaseConfig):
    """Convenience constructor to set Ethereum defaults for the chainlib cli config object
    """
    default_base_config_dir = os.path.join(script_dir, 'data', 'config')
    default_fee_limit = 21000

    @classmethod
    def from_args(cls, args, arg_flags=0x0f, env=os.environ, extra_args={}, base_config_dir=None, default_config_dir=None, user_config_dir=None, default_fee_limit=None, logger=None, load_callback=None):
        super(Config, cls).override_defaults(base_dir=cls.default_base_config_dir)
        if default_fee_limit == None:
            default_fee_limit = cls.default_fee_limit
        config = BaseConfig.from_args(args, arg_flags=arg_flags, env=env, extra_args=extra_args, base_config_dir=base_config_dir, default_config_dir=default_config_dir, user_config_dir=user_config_dir, default_fee_limit=default_fee_limit, logger=logger, load_callback=load_callback)

        if not config.get('RPC_DIALECT'):
            config.add('default', 'RPC_DIALECT', exists_ok=True)
        elif config.get('RPC_DIALECT') not in [
                'openethereum',
                'default',
                ]:
            raise ValueError('unknown rpc dialect {}'.format(config.get('RPC_DIALECT'))) 

        return config
