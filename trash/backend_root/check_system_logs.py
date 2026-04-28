from sqlalchemy import text
from app.core.database import engine

def check_logs():
    with engine.connect() as conn:
        try:
            res = conn.execute(text("SELECT id, level, message, created_at FROM system_logs ORDER BY id DESC LIMIT 20"))
            print(f"{'ID':<5} | {'Level':<10} | {'Message':<50} | {'Time'}")
            print("-" * 100)
            for row in res:
                msg = str(row[2])[:50]
                print(f"{row[0]:<5} | {row[1]:<10} | {msg:<50} | {row[3]}")
        except Exception as e:
            print(f"Error reading logs table: {e}")

if __name__ == "__main__":
    check_logs()
