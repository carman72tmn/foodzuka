import os
import sys

# Добавляем путь к backend в sys.path
sys.path.append(os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

from app.core.database import engine
from sqlalchemy import text

def check():
    with engine.connect() as conn:
        res = conn.execute(text("SELECT * FROM vk_bot_message_logs ORDER BY id DESC LIMIT 15")).fetchall()
        print("vk_bot_message_logs (last 15):")
        for r in res:
            # Поля: id, account_id, vk_message_id, event_type, text, status, error_text, created_at, sent_at
            print(f"ID: {r[0]} | Account ID: {r[1]} | Msg ID: {r[2]} | Event: {r[3]} | Status: {r[5]} | Sent: {r[8]}")
            print(f"Text: {r[4][:120]}...")
            if r[6]:
                print(f"Error: {r[6]}")
            print("-" * 50)

if __name__ == "__main__":
    check()
