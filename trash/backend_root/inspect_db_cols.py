import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check():
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'orders'"))
        columns = [row[0] for row in result]
        print("COLUMNS:" + ",".join(columns))

if __name__ == "__main__":
    asyncio.run(check())
