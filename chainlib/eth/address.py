# external imports
import sha3
from hexathon import (
        strip_0x,
        uniform,
    )
from crypto_dev_signer.encoding import (
        is_address,
        is_checksum_address,
        to_checksum_address,
        )

to_checksum = to_checksum_address


class AddressChecksum:
    """Address checksummer implementation.

    Primarily for use with chainlib.cli.wallet.Wallet
    """

    @classmethod
    def valid(cls, v):
        """Check if address is a valid checksum address

        :param v: Address value, in hex
        :type v: str
        :rtype: bool
        :returns: True if valid checksum
        """
        return is_checksum_address(v)


    @classmethod
    def sum(cls, v):
        """Create checksum from address

        :param v: Address value, in hex
        :type v: str
        :raises ValueError: Invalid address
        :rtype: str
        :returns: Checksum address
        """
        return to_checksum_address(v)
