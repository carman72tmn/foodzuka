from app.core.database import engine
from sqlalchemy import text

def migrate():
    print("Starting database migration to add courier/order fields...")
    queries = [
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS address_comment VARCHAR;",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS additional_info VARCHAR;",
        "ALTER TABLE orders ADD COLUMN IF NOT EXISTS other_info VARCHAR;"
    ]
    with engine.connect() as conn:
        with conn.begin():
            for query in queries:
                print(f"Executing: {query}")
                conn.execute(text(query))
    print("Migration finished successfully!")

if __name__ == "__main__":
    migrate()
