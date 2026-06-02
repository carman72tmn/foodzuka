from app.core.database import engine
from sqlalchemy import text
from sqlmodel import Session

sql = """
ALTER TABLE customers ADD COLUMN IF NOT EXISTS first_order_date TIMESTAMP WITHOUT TIME ZONE;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS total_discount NUMERIC(12, 2) DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS total_items FLOAT DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS average_check NUMERIC(12, 2) DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS frequency_days FLOAT DEFAULT 0;
ALTER TABLE customers ADD COLUMN IF NOT EXISTS days_since_last_order INTEGER;
"""

with Session(engine) as session:
    session.execute(text(sql))
    session.commit()
    print("Database updated successfully")
