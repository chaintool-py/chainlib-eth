from chainlib.cli.arg import ArgFlag as BaseArgFlag
from chainlib.cli.arg import Arg as BaseArg
from chainlib.cli.arg import ArgumentParser
from chainlib.cli.arg import process_args
from chainlib.cli.arg import stdin_arg


class ArgFlag(BaseArgFlag):
    pass
#
#    def __init__(self):
#        super(ArgFlag, self).__init__()
#
#        self.add('create')
# 
#
class Arg(BaseArg):
    pass
#
#    def __init__(self, flags):
#        super(Arg, self).__init__(flags)
#        self.add_long('null', 'create', typ=bool, help='Send to null-address (contract creation). Same as -a null or omitting -a.')
