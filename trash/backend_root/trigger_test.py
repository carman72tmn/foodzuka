import httpx
import asyncio
import json

async def trigger():
    async with httpx.AsyncClient(timeout=60.0) as client:
        print("Testing connection...")
        try:
            r = await client.post('http://localhost:8000/api/v1/iiko/test-connection')
            print(f"Test Connection: {r.status_code}")
            print(json.dumps(r.json(), indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Test Connection Error: {e}")

        print("\nTriggering menu sync...")
        try:
            r = await client.post('http://localhost:8000/api/v1/iiko/sync-menu')
            print(f"Sync Menu: {r.status_code}")
            print(json.dumps(r.json(), indent=2, ensure_ascii=False))
        except Exception as e:
            print(f"Sync Menu Error: {e}")

if __name__ == "__main__":
    asyncio.run(trigger())
