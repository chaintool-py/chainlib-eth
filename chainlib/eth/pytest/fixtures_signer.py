# standard imports
#import os

# external imports
import pytest


@pytest.fixture(scope='function')
def agent_roles(
        eth_accounts,
        ):
    return {
        'ALICE': eth_accounts[20],
        'BOB': eth_accounts[21],
        'CAROL': eth_accounts[23],
        'DAVE': eth_accounts[24],
        }
