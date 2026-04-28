import os
import sys
from sqlalchemy import create_engine, select, text

DATABASE_URL = "postgresql://foodtech_user:postgres@db:5432/foodtech_db"

def check_orders():
    engine = create_engine(DATABASE_URL)
    with engine.connect() as conn:
        print("\nLast 10 orders with dates:")
        res = conn.execute(text("SELECT id, external_number, status, created_at FROM orders ORDER BY created_at DESC LIMIT 10")).fetchall()
        for row in res:
            print(row)

if __name__ == "__main__":
    check_orders()
