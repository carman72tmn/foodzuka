import requests

url = "https://72roll.ru/api/v1/customers/275/sync"
try:
    response = requests.post(url, timeout=10)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")
except Exception as e:
    print(f"Error: {e}")
