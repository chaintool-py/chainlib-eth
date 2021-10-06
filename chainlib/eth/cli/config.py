# standard imports
import os

# external imports
from chainlib.cli import Config as BaseConfig

script_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(script_dir, '..')


class Config(BaseConfig):
    """Convenience constructor to set Ethereum defaults for the chainlib cli config object
    """
    default_base_config_dir = os.path.join(data_dir, 'data', 'config')
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

