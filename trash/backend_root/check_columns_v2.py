from app.core.database import engine
from sqlalchemy import inspect
import json

def check_columns():
    inspector = inspect(engine)
    columns = inspector.get_columns('delivery_zones')
    column_names = [col['name'] for col in columns]
    print(json.dumps(column_names))

if __name__ == "__main__":
    check_columns()
