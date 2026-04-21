import psycopg2
from app.core.config import settings

def check():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT enumlabel FROM pg_enum JOIN pg_type ON pg_enum.enumtypid = pg_type.oid WHERE pg_type.typname = 'orderstatus'")
    rows = cur.fetchall()
    print(f"Labels in orderstatus enum: {[row[0] for row in rows]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    check()
