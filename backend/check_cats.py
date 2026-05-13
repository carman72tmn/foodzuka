import asyncio
import os
import sys

# Добавляем путь к backend в sys.path
sys.path.append(os.getcwd())

from app.services.iiko_service import IikoService

async def main():
    iiko = IikoService()
    try:
        cats = await iiko.get_customer_categories()
        print("Categories found in iiko:")
        for cat in cats.get("guestCategories", []):
            print(f"- {cat.get('name')} (ID: {cat.get('id')})")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(main())
