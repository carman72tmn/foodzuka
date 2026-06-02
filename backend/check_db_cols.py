from app.core.database import engine
from sqlalchemy import inspect

def check_columns():
    inspector = inspect(engine)
    columns = inspector.get_columns('courier_orders')
    for column in columns:
        print(f"Column: {column['name']}, Type: {column['type']}")

if __name__ == "__main__":
    check_columns()
