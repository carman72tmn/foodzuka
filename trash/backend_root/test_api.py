import httpx
try:
    r = httpx.get('http://localhost:8000/api/v1/iiko/settings')
    print(f"Status: {r.status_code}")
    print(f"Body: {r.text[:200]}")
except Exception as e:
    print(f"Error: {e}")
