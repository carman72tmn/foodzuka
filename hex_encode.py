import binascii
import sys

with open(sys.argv[1], 'rb') as f:
    print(binascii.hexlify(f.read()).decode())
