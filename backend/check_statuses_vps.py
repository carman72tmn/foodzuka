import psycopg2
from app.core.config import settings

def check():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT status FROM orders")
    rows = cur.fetchall()
    print(f"Distinct statuses in DB: {[row[0] for row in rows]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    check()
