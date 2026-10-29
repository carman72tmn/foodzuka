import sys
from sqlalchemy import text
from app.core.database import engine

def migrate():
    with engine.connect() as conn:
        print('Creating table hidden_couriers if not exists...')
        conn.execute(text('''
            CREATE TABLE IF NOT EXISTS hidden_couriers (
                courier_iiko_id VARCHAR(100) PRIMARY KEY,
                courier_name VARCHAR(255),
                hidden_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
        '''))
        conn.commit()
        print('Migration hidden_couriers successfully applied!')

if __name__ == '__main__':
    migrate()
