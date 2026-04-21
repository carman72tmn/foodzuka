import psycopg2
from app.core.config import settings

def migrate():
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    # 1. Change column type to VARCHAR
    cur.execute("ALTER TABLE orders ALTER COLUMN status TYPE VARCHAR")
    print("Changed orders.status to VARCHAR")
    
    # 2. Try to drop the enum type if no other table uses it
    try:
        cur.execute("DROP TYPE orderstatus")
        print("Dropped orderstatus enum type")
    except Exception as e:
        print(f"Could not drop enum type (maybe in use): {e}")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()
