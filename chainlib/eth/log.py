# external imports
import sha3


class LogBloom:
    """Helper for Ethereum receipt log bloom filters.
    """
    def __init__(self):
        self.content = bytearray(256)


    def add(self, element):
        """Add topic element to filter.

        :param element: Topic element
        :type element: bytes
        """
        if not isinstance(element, bytes):
            raise ValueError('element must be bytes')
        h = sha3.keccak_256()
        h.update(element)
        z = h.digest()

        for j in range(3):
            c = j * 2
            v = int.from_bytes(z[c:c+2], byteorder='big')
            v &= 0x07ff
            m = 255 - int(v / 8)
            n = v % 8
            self.content[m] |= (1 << n)
