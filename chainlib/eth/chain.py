from chainlib.jsonrpc import JSONRPCRequest


def network_id(id_generator=None):
    j = JSONRPCRequest(id_generator=id_generator)
    o = j.template()
    o['method'] = 'net_version'
    return j.finalize(o)
