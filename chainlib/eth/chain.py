from chainlib.jsonrpc import JSONRPCRequest


def network_id(id_generator=None):
    """Generate json-rpc query to retrieve network id from node

    :param id_generator: JSON-RPC id generator
    :type id_generator: JSONRPCIdGenerator
    :rtype: dict
    :returns: rpc query object
    """
    j = JSONRPCRequest(id_generator=id_generator)
    o = j.template()
    o['method'] = 'net_version'
    return j.finalize(o)
