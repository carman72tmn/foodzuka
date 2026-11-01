import sys
import os

# Добавляем путь к корню бэкенда, чтобы импортировать базу данных
sys.path.append(os.path.join(os.path.dirname(__file__), "backend"))

from app.core.database import engine
from sqlalchemy import text

create_notifications_sql = """
CREATE TABLE IF NOT EXISTS admin_notifications (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    title VARCHAR(255) NOT NULL,
    body VARCHAR(1000) NOT NULL,
    url VARCHAR(500),
    event_type VARCHAR(100) NOT NULL,
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
"""

with engine.connect() as connection:
    print("Creating admin_notifications table...")
    connection.execute(text(create_notifications_sql))
    connection.commit()
    print("Database migration completed successfully!")
