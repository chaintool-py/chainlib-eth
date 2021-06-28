# standard imports
import sys
import select

# external imports
from hexathon import strip_0x

# local imports
from chainlib.eth.address import to_checksum_address

v = None
if len(sys.argv) > 1:
    v = sys.argv[1]
else:
    h = select.select([sys.stdin], [], [], 0)
    if len(h[0]) > 0:
        v = h[0][0].read()
        v = v.rstrip()

if v == None:
    sys.stderr.write('input missing\n')
    sys.exit(1)

def main():
    try:
        print(to_checksum_address(strip_0x(v)))
    except ValueError as e:
        sys.stderr.write('invalid input: {}\n'.format(e))
        sys.exit(1)


if __name__ == '__main__':
    main()
