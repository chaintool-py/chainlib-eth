# standard imports
import logging
import json

# external imports
from potaahto.symbols import snake_and_camel
from hexathon import (
        uniform,
        strip_0x,
        )

# local imports
from chainlib.src import (
        Src as BaseSrc,
        SrcItem,
        )

logg = logging.getLogger(__name__)


class Src(BaseSrc):

    @classmethod
    def src_normalize(self, v):
        src = snake_and_camel(v)
        if isinstance(src.get('v'), str):
            try:
                src['v'] = int(src['v'])
            except ValueError:
                src['v'] = int(src['v'], 16)
        return src


    def normal(self, v, typ=SrcItem.AUTO):
        if typ == SrcItem.SRC:
            return self.src_normalize(v)

        if typ == SrcItem.HASH:
            v = strip_0x(v, pad=False)
            v = uniform(v, compact_value=True)
        elif typ == SrcItem.ADDRESS:
            v = strip_0x(v, pad=False)
            v = uniform(v, compact_value=True)
        elif typ == SrcItem.PAYLOAD:
            v = strip_0x(v, pad=False, allow_empty=True)
            v = uniform(v, compact_value=False, allow_empty=True)

        return v


    def __repr__(self):
        return json.dumps(self.src)
