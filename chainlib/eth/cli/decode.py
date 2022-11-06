# external imports
from hexathon import (
        strip_0x,
        add_0x,
        )

# local imports
from chainlib.eth.tx import unpack
from chainlib.eth.tx import Tx


def decode_for_puny_humans(tx_raw, chain_spec, writer, fields=None, skip_keys=False):
    tx_raw = strip_0x(tx_raw)
    tx_raw_bytes = bytes.fromhex(tx_raw)
    tx_src = unpack(tx_raw_bytes, chain_spec)
    tx = Tx.from_src(tx_src, chain_spec=chain_spec)
    writer.write(tx.to_human(fields=fields, skip_keys=skip_keys))
    writer.write('\n')
