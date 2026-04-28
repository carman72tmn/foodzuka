import asyncio
import sys
import os

# Add backend to path
sys.path.append(os.path.join(os.getcwd(), "backend"))

async def main():
    try:
        from app.services.iiko_sync_service import sync_all
        print(">>> Triggering full sync_all()...")
        await sync_all()
        print(">>> Sync complete!")
    except Exception as e:
        print(f"!!! Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
