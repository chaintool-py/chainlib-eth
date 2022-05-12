# standard imports
import unittest
import os
import logging

# external imports
from aiee.arg import process_args

# local imports
#from chainlib.cli.base import argflag_std_base
from chainlib.eth.cli.arg import (
        ArgFlag,
        Arg,
        ArgumentParser,
        )
from chainlib.eth.cli.config import (
        Config,
        process_config,
        )
script_dir = os.path.dirname(os.path.realpath(__file__))
data_dir = os.path.join(script_dir, 'testdata')
config_dir = os.path.join(data_dir, 'config')

logging.basicConfig(level=logging.DEBUG)


class TestCli(unittest.TestCase):

    def setUp(self):
        self.flags = ArgFlag()
        self.arg = Arg(self.flags)


    def test_args_process_single(self):
        ap = ArgumentParser()
        flags = self.flags.VERBOSE | self.flags.CONFIG
        process_args(ap, self.arg, flags)

        argv = [
            '-vv',
            '-n',
            'foo',
                ]
        args = ap.parse_args(argv)
        config = Config(config_dir)
        config = process_config(config, self.arg, args, flags)
        self.assertEqual(config.get('CONFIG_USER_NAMESPACE'), 'foo')


if __name__ == '__main__':
    unittest.main()
