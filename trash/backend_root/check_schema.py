from app.core.database import engine
from sqlalchemy import inspect

inspector = inspect(engine)
columns = inspector.get_columns('delivery_zones')
for c in columns:
    print(f"Column: {c['name']}, Nullable: {c['nullable']}")
