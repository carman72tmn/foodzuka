import asyncio
import httpx

async def trigger_sync():
    # Attempt to trigger sync via local backend if running
    url = "http://localhost:8000/api/v1/employees/sync"
    print(f"Triggering sync at {url}...")
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(url)
            print(f"Status: {resp.status_code}")
            print(f"Response: {resp.text}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(trigger_sync())
