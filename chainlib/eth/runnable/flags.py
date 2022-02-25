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
        'encode': chainlib.eth.cli.argflag_std_write | chainlib.eth.cli.Flag.EXEC | chainlib.eth.cli.Flag.FEE | chainlib.eth.cli.Flag.FMT_HUMAN | chainlib.eth.cli.Flag.FMT_WIRE | chainlib.eth.cli.Flag.FMT_RPC,
        'count': chainlib.eth.cli.argflag_std_base_read | chainlib.eth.cli.Flag.WALLET,
        'raw': chainlib.eth.cli.argflag_std_write | chainlib.eth.cli.Flag.EXEC,
        'balance': chainlib.eth.cli.argflag_std_base | chainlib.eth.cli.Flag.WALLET,
        'wait': chainlib.eth.cli.argflag_reset(chainlib.eth.cli.argflag_std_base_read | chainlib.eth.cli.Flag.NO_TARGET | chainlib.eth.cli.Flag.RPC_AUTH, chainlib.eth.cli.Flag.CHAIN_SPEC | chainlib.eth.cli.Flag.RAW),
        'checksum': 0,
        }

if __name__ == '__main__':
    b = cmds[sys.argv[1]]
    print(add_0x(hex(b)))
