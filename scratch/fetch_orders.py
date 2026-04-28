import urllib.request
try:
    with urllib.request.urlopen('http://localhost:8000/api/v1/orders/') as response:
        print(response.read().decode())
except Exception as e:
    print(str(e))
