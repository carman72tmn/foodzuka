import psycopg2
from app.core.config import settings

def migrate():
    conn = psycopg2.connect(settings.DATABASE_URL)
    conn.autocommit = True
    cur = conn.cursor()
    
    # 1. Update records to uppercase
    cur.execute("UPDATE orders SET status = 'CLOSED' WHERE status = 'closed'")
    cur.execute("UPDATE orders SET status = 'CANCELLED' WHERE status = 'cancelled'")
    cur.execute("UPDATE orders SET status = 'NEW' WHERE status = 'new'")
    cur.execute("UPDATE orders SET status = 'CONFIRMED' WHERE status = 'confirmed'")
    cur.execute("UPDATE orders SET status = 'PREPARING' WHERE status = 'preparing'")
    cur.execute("UPDATE orders SET status = 'COOKING' WHERE status = 'cooking'")
    cur.execute("UPDATE orders SET status = 'READY' WHERE status = 'ready'")
    cur.execute("UPDATE orders SET status = 'DELIVERING' WHERE status = 'delivering'")
    cur.execute("UPDATE orders SET status = 'DELIVERED' WHERE status = 'delivered'")
    
    print("Updated order statuses to uppercase in DB")
    
    cur.close()
    conn.close()

if __name__ == "__main__":
    migrate()
