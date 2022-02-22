# standard imports
import sys

# external imports
import chainlib.eth.cli
from hexathon import add_0x

cmds = {
        'gas': chainlib.eth.cli.argflag_std_write | chainlib.eth.cli.Flag.WALLET,
        }

if __name__ == '__main__':
    b = cmds[sys.argv[1]]
    print(add_0x(hex(b)))
