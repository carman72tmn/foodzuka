import binascii
import sys

with open('backend/app/services/iiko_sync_service.py', 'rb') as f:
    hex_data = binascii.hexlify(f.read()).decode()
    with open('sync.hex', 'w') as out:
        out.write(hex_data)
