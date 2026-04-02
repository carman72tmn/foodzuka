import httpx
import asyncio

async def test_live():
    url = "https://72roll.ru/api/v1/employees"
    print(f"Testing {url}...")
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False, follow_redirects=True) as client:
            resp = await client.get(url)
            print(f"Status: {resp.status_code}")
            print(f"Final URL: {resp.url}")
            print(f"Response: {resp.text[:500]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_live())
