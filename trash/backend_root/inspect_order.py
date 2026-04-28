import asyncio
import json
from sqlalchemy import text
from app.core.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT order_items_details FROM orders WHERE id = 204"))
        row = result.first()
        if row:
            print("JSON_START")
            print(json.dumps(row[0], indent=2, ensure_ascii=False))
            print("JSON_END")

if __name__ == "__main__":
    asyncio.run(check())
