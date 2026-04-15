from sqlalchemy import text
from app.core.database import engine

def migrate():
    with engine.connect() as conn:
        print("Alter columns in orders...")
        conn.execute(text("ALTER TABLE orders ALTER COLUMN telegram_user_id DROP NOT NULL"))
        conn.execute(text("ALTER TABLE orders ALTER COLUMN telegram_username DROP NOT NULL"))
        conn.execute(text("ALTER TABLE orders ALTER COLUMN customer_name DROP NOT NULL"))
        conn.execute(text("ALTER TABLE orders ALTER COLUMN customer_phone DROP NOT NULL"))
        conn.execute(text("ALTER TABLE orders ALTER COLUMN delivery_address DROP NOT NULL"))
        
        print("Alter columns in order_items...")
        conn.execute(text("ALTER TABLE order_items ALTER COLUMN product_id DROP NOT NULL"))
        conn.commit()
    print("Migration successful")

if __name__ == "__main__":
    migrate()
