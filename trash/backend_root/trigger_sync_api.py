import urllib.request
import json
import sys

try:
    req = urllib.request.Request("http://localhost:8000/api/v1/orders/sync", method="POST")
    with urllib.request.urlopen(req) as response:
        status = response.getcode()
        body = response.read().decode('utf-8')
        print(f"Status Code: {status}")
        print(f"Response: {body}")
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
