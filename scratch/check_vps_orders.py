import sys
import os
import json
from datetime import datetime

# Добавляем путь к приложению
sys.path.append('/app')

try:
    from app.core.database import Session, engine
    from sqlmodel import text

    with Session(engine) as session:
        # Check sync_logs for recent errors
        print("--- SYNC LOGS (LAST 5) ---")
        try:
            res = session.execute(text("SELECT * FROM sync_logs ORDER BY created_at DESC LIMIT 5")).fetchall()
            for row in res:
                print(row)
        except Exception as e:
            print(f"Error reading sync_logs: {e}")

        session.rollback() # Reset transaction

        # Check recent orders and their statuses
        print("\n--- RECENT ORDERS (LAST 5) ---")
        try:
            res = session.execute(text("SELECT id, iiko_id, status, iiko_status, updated_at FROM orders ORDER BY created_at DESC LIMIT 5")).fetchall()
            for row in res:
                print(row)
        except Exception as e:
            print(f"Error reading orders: {e}")
            
except Exception as e:
    print(f"Error: {e}")
