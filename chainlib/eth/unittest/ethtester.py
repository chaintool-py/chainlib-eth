# standard imports
import os
import unittest
import logging

# external imports
import eth_tester
from crypto_dev_signer.eth.signer import ReferenceSigner as EIP155Signer
from crypto_dev_signer.keystore.dict import DictKeystore
from hexathon import (
        strip_0x,
        add_0x,
        )
from eth import constants
from eth.vm.forks.byzantium import ByzantiumVM

# local imports
from .base import (
        EthTesterSigner,
        TestRPCConnection,
        )
from chainlib.connection import (
        RPCConnection,
        ConnType,
        )
from chainlib.eth.address import to_checksum_address
from chainlib.chain import ChainSpec

logg = logging.getLogger(__name__)

test_address = bytes.fromhex('Eb3907eCad74a0013c259D5874AE7f22DcBcC95C')


def create_tester_signer(keystore):
    genesis_params = eth_tester.backends.pyevm.main.get_default_genesis_params({
        'gas_limit': 8000000,
        'coinbase': test_address, # doesn't seem to work
        })
    vm_configuration = (
                (constants.GENESIS_BLOCK_NUMBER, ByzantiumVM),
    )
    genesis_state = eth_tester.PyEVMBackend._generate_genesis_state(num_accounts=30)
    eth_backend = eth_tester.PyEVMBackend(
            genesis_state=genesis_state,
            genesis_parameters=genesis_params,
            vm_configuration=vm_configuration,
            )
    return EthTesterSigner(eth_backend, keystore)


class EthTesterCase(unittest.TestCase):

    def __init__(self, foo):
        super(EthTesterCase, self).__init__(foo)
        self.accounts = []


    def setUp(self):
        self.chain_spec = ChainSpec('evm', 'foochain', 42)
        self.keystore = DictKeystore()
        eth_tester_instance = create_tester_signer(self.keystore)
        self.signer = EIP155Signer(self.keystore)
        self.helper = eth_tester_instance
        self.backend = self.helper.backend
        self.rpc = TestRPCConnection(None, eth_tester_instance, self.signer)
        for a in self.keystore.list():
            self.accounts.append(add_0x(to_checksum_address(a)))

        def rpc_with_tester(chain_spec=self.chain_spec, url=None):
            return self.rpc

        RPCConnection.register_constructor(ConnType.CUSTOM, rpc_with_tester, tag='default')
        RPCConnection.register_constructor(ConnType.CUSTOM, rpc_with_tester, tag='signer')
        RPCConnection.register_location('custom', self.chain_spec, tag='default', exist_ok=True)
        RPCConnection.register_location('custom', self.chain_spec, tag='signer', exist_ok=True)

        

    def tearDown(self):
        pass
