# proposed custom errors
# source: https://eth.wiki/json-rpc/json-rpc-error-codes-improvement-proposal

#1   Unauthorized    Should be used when some action is not authorized, e.g. sending from a locked account.
#2   Action not allowed  Should be used when some action is not allowed, e.g. preventing an action, while another depending action is processing on, like sending again when a confirmation popup is shown to the user (?).
#3   Execution error Will contain a subset of custom errors in the data field. See below.

#100 X doesn’t exist Should be used when something which should be there is not found. (Doesn’t apply to eth_getTransactionBy_ and eth_getBlock_. They return a success with value null)
#101 Requires ether  Should be used for actions which require somethin else, e.g. gas or a value.
#102 Gas too low Should be used when a to low value of gas was given.
#103 Gas limit exceeded  Should be used when a limit is exceeded, e.g. for the gas limit in a block.
#104 Rejected    Should be used when an action was rejected, e.g. because of its content (too long contract code, containing wrong characters ?, should differ from -32602 - Invalid params).
#105 Ether too low   Should be used when a to low value of Ether was given.

#106 Timeout Should be used when an action timedout.
#107 Conflict    Should be used when an action conflicts with another (ongoing?) action.

# external imports
from hexathon import add_0x


def to_blockheight_param(height):
    """Translate blockheight specifier to Ethereum json-rpc blockheight argument.

    :param height: Height argument
    :type height: any
    :rtype: str
    :returns: Argument value
    """
    if height == None:
        height = 'latest'
    elif isinstance(height, str):
        try:
            height = int(height)
        except ValueError:
            pass
    if isinstance(height, int):
        if height == 0:
            height = 'latest'
        elif height < 0:
            height = 'pending'
        else:
            height = add_0x(int(height).to_bytes(8, 'big').hex())
    return height 
