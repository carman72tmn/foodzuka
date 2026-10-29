"""
Скрипт для создания оптимизированных индексов таблицы multichat_messages
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlmodel import Session, text
from app.core.database import engine

def create_indexes():
    queries = [
        "CREATE INDEX IF NOT EXISTS ix_multichat_msg_channel_peer_id_desc ON multichat_messages (channel, peer_id, id DESC);",
        "CREATE INDEX IF NOT EXISTS ix_multichat_unread_inbound ON multichat_messages (direction, is_read) WHERE direction = 'inbound' AND is_read = false;",
        "CREATE INDEX IF NOT EXISTS ix_multichat_channel_peer_read ON multichat_messages (channel, peer_id, is_read);"
    ]
    with Session(engine) as session:
        for q in queries:
            print(f"Executing: {q}")
            session.exec(text(q))
        session.commit()
    print("All multichat indexes created successfully!")

if __name__ == "__main__":
    create_indexes()
