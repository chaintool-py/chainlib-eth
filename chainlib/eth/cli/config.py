# standard imports
import os

# external imports
from chainlib.cli.config import (
        Config as BaseConfig,
        process_config as base_process_config,
        )


script_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(script_dir, '..')


class Config(BaseConfig):
    """Convenience constructor to set Ethereum defaults for the chainlib cli config object
    """
    default_base_config_dir = os.path.join(data_dir, 'data', 'config')
    default_fee_limit = 21000


def process_config(config, arg, args, flags, positional_name=None):
    config = base_process_config(config, arg, args, flags, positional_name=positional_name)
#    if arg.match('provider', flags):
#        if not bool(config.get('RPC_DIALECT')):
#            config.add('default', 'RPC_DIALECT', exists_ok=True)
#        elif config.get('RPC_DIALECT') not in [
#                'openethereum',
#                'default',
#                ]:
#            raise ValueError('unknown rpc dialect {}'.format(config.get('RPC_DIALECT'))) 

    #if arg.match('create', flags):
    #    config.add(getattr(args, 'null'), '_NULL')


    return config
