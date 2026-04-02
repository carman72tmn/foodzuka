import os
from sqlalchemy import create_engine, text

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://foodtech_user:your_strong_password@db:5432/foodtech_db")
engine = create_engine(DATABASE_URL)

def debug_db():
    with engine.connect() as conn:
        print(f"Connected to: {DATABASE_URL}")
        
        # Check schemas for 'orders' table
        print("\nChecking schemas for 'orders' table:")
        query = text("SELECT table_schema, table_name FROM information_schema.tables WHERE table_name = 'orders'")
        results = conn.execute(query).fetchall()
        for row in results:
            print(f"Schema: {row[0]}, Table: {row[1]}")
            
        # Check columns in public.orders
        print("\nColumns in public.orders:")
        query = text("SELECT column_name FROM information_schema.columns WHERE table_schema = 'public' AND table_name = 'orders'")
        results = conn.execute(query).fetchall()
        cols = [row[0] for row in results]
        print(", ".join(cols))
        
        # Check columns in any other schema found
        for row in results:
            schema = row[0]
            if schema != 'public':
                print(f"\nColumns in {schema}.orders:")
                query = text(f"SELECT column_name FROM information_schema.columns WHERE table_schema = '{schema}' AND table_name = 'orders'")
                results2 = conn.execute(query).fetchall()
                cols2 = [r[0] for r in results2]
                print(", ".join(cols2))

if __name__ == "__main__":
    debug_db()
