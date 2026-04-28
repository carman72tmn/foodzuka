from app.core.database import engine
from sqlmodel import SQLModel
from app.models.user import User
from app.models.role import Role
import sqlalchemy as sa

def migrate():
    with engine.begin() as conn:
        # Create all tables defined in SQLModel metadata
        print("Creating all missing tables...")
        SQLModel.metadata.create_all(conn)
        
        # Add columns to users table if not exists
        inspector = sa.inspect(conn)
        columns = [c['name'] for c in inspector.get_columns('users')]
        
        if 'role_id' not in columns:
            print("Adding role_id column to users table...")
            conn.execute(sa.text("ALTER TABLE users ADD COLUMN role_id INTEGER REFERENCES roles(id)"))
            
        if 'iiko_id' not in columns:
            print("Adding iiko_id column to users table...")
            conn.execute(sa.text("ALTER TABLE users ADD COLUMN iiko_id UUID"))

        if 'full_name' not in columns:
            print("Adding full_name column to users table...")
            conn.execute(sa.text("ALTER TABLE users ADD COLUMN full_name VARCHAR"))
            
        role_columns = [c['name'] for c in inspector.get_columns('roles')]
        if 'code' not in role_columns:
            print("Adding code column to roles table...")
            conn.execute(sa.text("ALTER TABLE roles ADD COLUMN code VARCHAR UNIQUE"))

    print("Migration completed successfully.")

if __name__ == "__main__":
    migrate()
