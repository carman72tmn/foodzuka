import httpx
import asyncio

async def test_get():
    # Attempt to reach the backend locally
    # We'll try 8000 (direct) and 80 (nginx)
    urls = [
        "http://localhost:8000/api/v1/employees",
        "http://127.0.0.1:8000/api/v1/employees",
        "http://192.168.31.162:8000/api/v1/employees",
        "http://192.168.31.162/api/v1/employees"
    ]
    
    for url in urls:
        print(f"Testing {url}...")
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                resp = await client.get(url)
                print(f"Status: {resp.status_code}")
                print(f"Response: {resp.text[:200]}...")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_get())
