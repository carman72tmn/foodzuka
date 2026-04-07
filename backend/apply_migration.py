import os
from sqlmodel import Session, create_engine, text
from app.models.delivery_zone import DeliveryZone

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://foodtech:foodtech@db:5432/foodtech")
engine = create_engine(DATABASE_URL)

def apply_migration():
    with Session(engine) as session:
        print("Checking for existing columns in delivery_zones...")
        try:
            session.exec(text("ALTER TABLE delivery_zones ADD COLUMN IF NOT EXISTS description TEXT"))
            session.exec(text("ALTER TABLE delivery_zones ADD COLUMN IF NOT EXISTS additional_info JSONB"))
            session.commit()
            print("Successfully added description and additional_info columns to delivery_zones table.")
        except Exception as e:
            print(f"Error applying migration: {e}")
            session.rollback()

if __name__ == "__main__":
    apply_migration()
