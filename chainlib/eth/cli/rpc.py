# external imports
from chainlib.cli import Rpc as BaseRpc
from chainlib.eth.connection import EthHTTPConnection

# local imports
from chainlib.eth.gas import (
        OverrideGasOracle,
        RPCGasOracle,
        )
from chainlib.eth.nonce import (
        OverrideNonceOracle,
        RPCNonceOracle,
        )


# TODO: how is the keystore implemented in rpc here?
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
