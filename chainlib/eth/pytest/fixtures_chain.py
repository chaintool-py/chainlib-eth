# external imports
import pytest

# local imports
from chainlib.chain import ChainSpec


@pytest.fixture(scope='session')
def default_chain_spec():
    return ChainSpec('evm', 'foo', 42)


@pytest.fixture(scope='session')
def default_chain_config():
    return {
        'foo': 42,
            }
