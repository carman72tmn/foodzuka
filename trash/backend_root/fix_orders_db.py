import os
from sqlalchemy import create_engine, text
from sqlalchemy.exc import ProgrammingError

# Database connection URL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://foodzuka:foodzuka_pass@foodtech-db:5432/foodzuka")

engine = create_engine(DATABASE_URL)
print(f"Connecting to: {DATABASE_URL}")

def add_column_if_not_exists(table_name, column_name, column_type, default_value=None):
    with engine.connect() as conn:
        try:
            # Check if column exists
            query = text(f"SELECT column_name FROM information_schema.columns WHERE table_name='{table_name}' AND column_name='{column_name}'")
            result = conn.execute(query).fetchone()
            
            if not result:
                print(f"Adding column {column_name} to {table_name}...")
                alter_query = f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}"
                if default_value is not None:
                    alter_query += f" DEFAULT {default_value}"
                
                conn.execute(text(alter_query))
                conn.commit()
                print(f"Column {column_name} added successfully.")
            else:
                print(f"Column {column_name} already exists in {table_name}.")
        except Exception as e:
            print(f"Error adding column {column_name}: {e}")

if __name__ == "__main__":
    print("Starting database fix for orders table...")
    
    # Numeric columns with default 0
    numeric_cols = [
        "bonus_accrued", "total_with_discount"
    ]
    for col in numeric_cols:
        add_column_if_not_exists("orders", col, "NUMERIC(10, 2)", "0.00")
    
    # String columns
    string_cols = [
        "payment_method", "order_type", "courier_name", "admin_name", "delivery_zone"
    ]
    for col in string_cols:
        add_column_if_not_exists("orders", col, "VARCHAR(255)")
    
    # DateTime columns
    datetime_cols = [
        "iiko_creation_time", "expected_time", "actual_time"
    ]
    for col in datetime_cols:
        add_column_if_not_exists("orders", col, "TIMESTAMP")
    
    # Integer columns
    add_column_if_not_exists("orders", "delay_minutes", "INTEGER")
    
    # Boolean columns
    add_column_if_not_exists("orders", "is_on_time", "BOOLEAN", "TRUE")
    
    # JSON columns
    json_cols = [
        "order_items_details", "discounts_details", "customer_info_details"
    ]
    for col in json_cols:
        add_column_if_not_exists("orders", col, "JSONB")
        
    print("Database fix for orders table completed.")
