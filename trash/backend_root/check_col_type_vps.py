import psycopg2
from app.core.config import settings

def check():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT column_name, data_type, udt_name FROM information_schema.columns WHERE table_name = 'orders' AND column_name = 'status'")
    row = cur.fetchone()
    print(f"Column: {row[0]}, Type: {row[1]}, UDT: {row[2]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    check()
