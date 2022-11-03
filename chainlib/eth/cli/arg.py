from chainlib.cli.arg import (
    ArgumentParser,
    Arg as BaseArg,
    ArgFlag as BaseArgFlag,
    process_args,
    stdin_arg,
    )


class ArgFlag(BaseArgFlag):

    def __init__(self):
        super(ArgFlag, self).__init__()

        self.add('create')
 

class Arg(BaseArg):

    def __init__(self, flags):
        super(Arg, self).__init__(flags)
        self.add_long('null', 'create', typ=bool, help='Send to null-address (contract creation). Same as -a null.')
