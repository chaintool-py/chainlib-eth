# standard imports
import os
import logging

# external imports
import eth_tester
import pytest
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer
from crypto_dev_signer.keystore.dict import DictKeystore

# local imports
from chainlib.eth.unittest.base import *
from chainlib.connection import (
        RPCConnection,
        ConnType,
        )
from chainlib.eth.unittest.ethtester import create_tester_signer
from chainlib.eth.address import to_checksum_address

logg = logging.getLogger(__name__)


@pytest.fixture(scope='function')
def eth_keystore():
    return DictKeystore()


@pytest.fixture(scope='function')
def init_eth_tester(
        eth_keystore,
        ):
    return create_tester_signer(eth_keystore) 


@pytest.fixture(scope='function')
def call_sender(
        eth_accounts,
        ):
    return eth_accounts[0]


@pytest.fixture(scope='function')
def eth_rpc(
        default_chain_spec,
        init_eth_rpc,
        ):
    return RPCConnection.connect(default_chain_spec, 'default')


@pytest.fixture(scope='function')
def eth_accounts(
        init_eth_tester,
        ):
    addresses = list(init_eth_tester.get_accounts())
    for address in addresses:
        balance = init_eth_tester.get_balance(address)
        logg.debug('prefilled account {} balance {}'.format(address, balance))
    return addresses


@pytest.fixture(scope='function')
def eth_empty_accounts(
        eth_keystore,
        init_eth_tester,
        ):
    a = []
    for i in range(10):
        #address = init_eth_tester.new_account()
        address = eth_keystore.new()
        checksum_address = add_0x(to_checksum_address(address))
        a.append(checksum_address)
        logg.info('added address {}'.format(checksum_address))
    return a


@pytest.fixture(scope='function')
def eth_signer(
        eth_keystore,
        ):
    return EIP155Signer(eth_keystore)


@pytest.fixture(scope='function')
def init_eth_rpc(
        default_chain_spec,
        init_eth_tester,
        eth_signer,
        ):

    rpc_conn = TestRPCConnection(None, init_eth_tester, eth_signer)
    def rpc_with_tester(url=None, chain_spec=default_chain_spec):
        return rpc_conn

    RPCConnection.register_constructor(ConnType.CUSTOM, rpc_with_tester, tag='default')
    RPCConnection.register_constructor(ConnType.CUSTOM, rpc_with_tester, tag='signer')
    RPCConnection.register_location('custom', default_chain_spec, tag='default', exist_ok=True)
    RPCConnection.register_location('custom', default_chain_spec, tag='signer', exist_ok=True)
    return None
