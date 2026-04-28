
import requests
import json

URL = "http://localhost:8000/api/v1/orders/"
try:
    response = requests.get(URL)
    if response.ok:
        orders = response.json()
        if orders:
            print(json.dumps(orders[0], indent=2, ensure_ascii=False))
        else:
            print("No orders found")
    else:
        print(f"Error: {response.status_code}")
except Exception as e:
    print(f"Connection error: {e}")
