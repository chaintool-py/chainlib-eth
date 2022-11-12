# standard imports
import sys

# external imports
from chainlib.eth.cli.arg import ArgFlag
from hexathon import add_0x


cmds = {
        'gas': [['std_write', 'wallet', 'value'], []],
        'info' : [['std_base_read'], ['chain_spec']],
        'get' : [['std_base_read', 'tab'], ['chain_spec']],
        'decode': [['std_base', 'chain_spec'], []],
        'encode': [['std_write', 'exec' ,'fee', 'fmt_human', 'fmt_wire', 'fmt_rpc'], []],
        'count' : [['std_base_read', 'wallet'], []],
        'raw': [['std_write', 'exec'], []],
        'balance': [['std_base', 'wallet'], []],
        'wait': [['std_base_read', 'target', 'rpc_auth'], ['chain_spec', 'raw']],
        'checksum': [[], []],
        }


if __name__ == '__main__':
    args = ArgFlag()
    r = 0
    instructions = cmds[sys.argv[1]]
    for k in instructions[0]:
        v = args.get(k)
        r = args.more(r, v)
    for k in instructions[1]:
        v = args.get(k)
        r = args.less(r, v)
    print(add_0x(hex(r)))
