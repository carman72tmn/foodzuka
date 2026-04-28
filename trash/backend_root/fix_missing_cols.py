from sqlmodel import Session, create_engine, text
import os

# Get DB URL from ENV or use default
db_url = os.environ.get("DATABASE_URL", "postgresql://foodtech:foodtech@db:5432/foodtech")
engine = create_engine(db_url)

with Session(engine) as session:
    try:
        # Add missing columns to employees table
        session.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS email VARCHAR(255);"))
        session.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS status VARCHAR(100);"))
        session.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS rate FLOAT;"))
        session.execute(text("ALTER TABLE employees ADD COLUMN IF NOT EXISTS document_info JSONB;"))
        session.commit()
        print("Missing columns (email, status, rate) successfully added to employees table.")
    except Exception as e:
        print(f"Error adding columns: {e}")
        session.rollback()
