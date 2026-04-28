import asyncio
import os
import sys

# Добавляем путь к приложению
sys.path.append("/app")

async def test_max_revision():
    print("STARTING TEST SCRIPT", flush=True)
    from app.services.iiko_service import iiko_service
    print(f"DEBUG: iiko_service class: {iiko_service.__class__}", flush=True)
    
    print("Testing safe get_max_revision...", flush=True)
    try:
        max_rev = await iiko_service.get_max_revision()
        print(f"SUCCESS! Resulting Max Revision: {max_rev}", flush=True)
    except Exception as e:
        print(f"FAILED with error: {e}", flush=True)

if __name__ == "__main__":
    asyncio.run(test_max_revision())
