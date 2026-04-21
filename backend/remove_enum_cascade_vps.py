import psycopg2
from app.core.config import settings

def migrate():
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    # 1. Remove default value
    cur.execute("ALTER TABLE orders ALTER COLUMN status DROP DEFAULT")
    
    # 2. Change column type to VARCHAR
    cur.execute("ALTER TABLE orders ALTER COLUMN status TYPE VARCHAR")
    print("Changed orders.status to VARCHAR")
    
    # 3. Drop the enum type with CASCADE
    cur.execute("DROP TYPE IF EXISTS orderstatus CASCADE")
    print("Dropped orderstatus enum type (CASCADE)")
    
    # 4. Set new default value as string
    cur.execute("ALTER TABLE orders ALTER COLUMN status SET DEFAULT 'new'")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()
