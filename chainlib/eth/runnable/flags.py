# standard imports
import sys

# external imports
import chainlib.eth.cli
from hexathon import add_0x

cmds = {
        'gas': chainlib.eth.cli.argflag_std_write | chainlib.eth.cli.Flag.WALLET,
        'info': chainlib.eth.cli.argflag_reset(chainlib.cli.argflag_std_base_read, chainlib.eth.cli.Flag.CHAIN_SPEC),
        'get': chainlib.eth.cli.argflag_reset(chainlib.cli.argflag_std_base_read, chainlib.eth.cli.Flag.CHAIN_SPEC),
        'decode': chainlib.cli.argflag_std_base | chainlib.eth.cli.Flag.CHAIN_SPEC,
        }

if __name__ == '__main__':
    b = cmds[sys.argv[1]]
    print(add_0x(hex(b)))
