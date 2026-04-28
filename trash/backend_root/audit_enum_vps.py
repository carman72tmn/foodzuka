import psycopg2
from app.core.config import settings

def check():
    conn = psycopg2.connect(settings.DATABASE_URL)
    cur = conn.cursor()
    cur.execute("SELECT n.nspname, t.typname, e.enumlabel FROM pg_enum e JOIN pg_type t ON e.enumtypid = t.oid JOIN pg_namespace n ON t.typnamespace = n.oid WHERE t.typname = 'orderstatus' ORDER BY n.nspname, e.enumsortorder")
    rows = cur.fetchall()
    for row in rows:
        print(f"Schema: {row[0]}, Type: {row[1]}, Label: {row[2]}")
    cur.close()
    conn.close()

if __name__ == "__main__":
    check()
