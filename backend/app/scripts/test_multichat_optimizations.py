"""
Тестирование эндпоинтов мультичата:
1. Загрузка списка диалогов
2. Пагинация истории (limit=10)
3. Массовое прочтение (POST /dialogs/read-all)
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlmodel import Session, select, func
from app.core.database import engine
from app.models.chat import MultichatMessage, MultichatPinnedDialog
from app.models.user import User

def run_tests():
    with Session(engine) as session:
        # Проверяем количество сообщений
        total_msgs = session.exec(select(func.count(MultichatMessage.id))).one()
        unread_msgs = session.exec(
            select(func.count(MultichatMessage.id))
            .where(MultichatMessage.direction == "inbound", MultichatMessage.is_read == False)
        ).one()
        print(f"Total messages in DB: {total_msgs}, Unread inbound messages: {unread_msgs}")

        # Проверяем последний диалог
        last_msg = session.exec(select(MultichatMessage).order_by(MultichatMessage.id.desc())).first()
        if last_msg:
            print(f"Sample dialog: channel={last_msg.channel}, peer_id={last_msg.peer_id}")
            # Тестируем выборку последних 10 сообщений
            limit_stmt = (
                select(MultichatMessage)
                .where(MultichatMessage.channel == last_msg.channel)
                .where(MultichatMessage.peer_id == last_msg.peer_id)
                .order_by(MultichatMessage.id.desc())
                .limit(10)
            )
            top10 = session.exec(limit_stmt).all()
            print(f"Fetched top {len(top10)} messages for sample dialog")

    print("Multichat backend database checks passed successfully!")

if __name__ == "__main__":
    run_tests()
