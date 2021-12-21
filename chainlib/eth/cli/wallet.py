# external imports
from funga.eth.signer import EIP155Signer
from funga.eth.keystore.dict import DictKeystore
from chainlib.cli import Wallet as BaseWallet

# local imports
from chainlib.eth.address import AddressChecksum


class Wallet(BaseWallet):
    """Convenience constructor to set Ethereum defaults for chainlib cli Wallet object

    :param checksummer: Address checksummer object
    :type checksummer: Implementation of chainlib.eth.address.AddressChecksum
    """
    def __init__(self, checksummer=AddressChecksum):
        super(Wallet, self).__init__(EIP155Signer, checksummer=checksummer, keystore=DictKeystore())



