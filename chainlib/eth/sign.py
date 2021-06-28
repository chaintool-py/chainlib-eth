# local imports
from chainlib.jsonrpc import JSONRPCRequest


def new_account(passphrase='', id_generator=None):
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'personal_newAccount'
    o['params'] = [passphrase]
    return j.finalize(o)


def sign_transaction(payload, id_generator=None):
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_signTransaction'
    o['params'] = [payload]
    return j.finalize(o)


def sign_message(address, payload, id_generator=None):
    j = JSONRPCRequest(id_generator)
    o = j.template()
    o['method'] = 'eth_sign'
    o['params'] = [address, payload]
    return j.finalize(o)
