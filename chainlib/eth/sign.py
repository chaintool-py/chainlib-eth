# local imports
from chainlib.jsonrpc import JSONRPCRequest


def new_account(passphrase='', id_generator=None):
    """Generate json-rpc query to create new account in keystore.

    Uses the personal_newAccount rpc call.

    :param passphrase: Passphrase string
    :type passphrase: str
    :param id_generator: JSONRPC id generator
    :type id_generator: JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'personal_newAccount'
    o['params'] = [passphrase]
    return j.finalize(o)


def sign_transaction(payload, id_generator=None):
    """Generate json-rpc query to sign transaction using the node keystore.

    The node must have the private key corresponding to the from-field in the transaction object.

    :param payload: Transaction
    :type payload: dict
    :param id_generator: JSONRPC id generator
    :type id_generator: JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_signTransaction'
    o['params'] = [payload]
    return j.finalize(o)


def sign_message(address, payload, id_generator=None):
    """Generate json-rpc query to sign an arbirary message using the node keystore.

    The node must have the private key corresponding to the address parameter.

    :param address: Address of key to sign with, in hex
    :type address: str
    :param payload: Arbirary message, in hex
    :type payload: str
    :param id_generator: JSONRPC id generator
    :type id_generator: JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_sign'
    o['params'] = [address, payload]
    return j.finalize(o)
