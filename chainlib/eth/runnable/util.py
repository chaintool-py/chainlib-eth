# local imports
from chainlib.eth.tx import unpack
from hexathon import (
        strip_0x,
        add_0x,
        )

def decode_out(tx, writer, skip_keys=[]):
    for k in tx.keys():
        if k in skip_keys:
            continue
        x = None
        if k == 'value':
            x = '{:.18f} eth'.format(tx[k] / (10**18))
        elif k == 'gasPrice':
            x = '{} gwei'.format(int(tx[k] / (10**9)))
        elif k == 'value':
            k = 'gas-value'
        if x != None:
            writer.write('{}: {} ({})\n'.format(k, tx[k], x))
        else:
            writer.write('{}: {}\n'.format(k, tx[k]))


def decode_for_puny_humans(tx_raw, chain_spec, writer, skip_keys=[]):
    tx_raw = strip_0x(tx_raw)
    tx_raw_bytes = bytes.fromhex(tx_raw)
    tx = unpack(tx_raw_bytes, chain_spec)
    decode_out(tx, writer, skip_keys=skip_keys)
    writer.write('src: {}\n'.format(add_0x(tx_raw)))

