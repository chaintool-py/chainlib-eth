from chainlib.cli.arg import (
    ArgumentParser,
    Arg as BaseArg,
    ArgFlag,
    process_args,
    stdin_arg,
    )


class Arg(BaseArg):

    def __init__(self, flags):
        super(Arg, self).__init__(flags)
        self.add('z', 'wallet', typ=bool, help='Send to null address (contract creation)')
