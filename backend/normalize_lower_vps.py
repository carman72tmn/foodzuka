import psycopg2
from app.core.config import settings

def migrate():
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    # 1. Update records to lowercase
    cur.execute("UPDATE orders SET status = 'closed' WHERE status = 'CLOSED'")
    cur.execute("UPDATE orders SET status = 'cancelled' WHERE status = 'CANCELLED'")
    cur.execute("UPDATE orders SET status = 'new' WHERE status = 'NEW'")
    cur.execute("UPDATE orders SET status = 'confirmed' WHERE status = 'CONFIRMED'")
    cur.execute("UPDATE orders SET status = 'preparing' WHERE status = 'PREPARING'")
    cur.execute("UPDATE orders SET status = 'cooking' WHERE status = 'COOKING'")
    cur.execute("UPDATE orders SET status = 'ready' WHERE status = 'READY'")
    cur.execute("UPDATE orders SET status = 'delivering' WHERE status = 'DELIVERING'")
    cur.execute("UPDATE orders SET status = 'delivered' WHERE status = 'DELIVERED'")
    
    print("Updated order statuses to lowercase in DB")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()
