import psycopg2
from app.core.config import settings

def migrate():
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    statuses = [
        'new', 'unconfirmed', 'confirmed', 'preparing', 'cooking', 
        'ready', 'ready_for_pickup', 'delivering', 'delivered', 
        'closed', 'cancelled'
    ]
    
    for status in statuses:
        try:
            cur.execute(f"ALTER TYPE orderstatus ADD VALUE IF NOT EXISTS '{status}'")
            print(f"Added value '{status}' to orderstatus enum")
        except Exception as e:
            print(f"Error adding '{status}': {e}")
            
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()
