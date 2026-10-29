"""
Тест быстрого Loose Index Scan с фильтрацией каналов на выходе
"""
import sys
import os
import time

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from sqlmodel import Session, text
from app.core.database import engine

def test_fast_filter():
    with Session(engine) as db:
        sql = """
            WITH RECURSIVE dialog_pairs AS (
                (
                    SELECT channel, peer_id
                    FROM multichat_messages
                    ORDER BY channel, peer_id
                    LIMIT 1
                )
                UNION ALL
                SELECT next_pair.channel, next_pair.peer_id
                FROM dialog_pairs prev
                CROSS JOIN LATERAL (
                    SELECT m.channel, m.peer_id
                    FROM multichat_messages m
                    WHERE (m.channel, m.peer_id) > (prev.channel, prev.peer_id)
                    ORDER BY m.channel, m.peer_id
                    LIMIT 1
                ) next_pair
            ),
            last_msgs AS (
                SELECT lm.*
                FROM dialog_pairs dp
                CROSS JOIN LATERAL (
                    SELECT *
                    FROM multichat_messages m
                    WHERE m.channel = dp.channel AND m.peer_id = dp.peer_id
                    ORDER BY m.id DESC
                    LIMIT 1
                ) lm
            )
            SELECT * FROM last_msgs 
            WHERE (:channel = 'all' 
               OR (:channel = 'vk' AND channel IN ('vk', 'vk_user'))
               OR (:channel = 'max' AND channel IN ('max', 'max_account', 'max_user', 'max_bot', 'max_bridge'))
               OR (:channel = 'whatsapp' AND channel IN ('whatsapp', 'whatsapp_account'))
               OR (:channel = 'telegram_bot' AND channel IN ('telegram_bot', 'telegram_user'))
               OR channel = :channel)
            ORDER BY created_at DESC;
        """
        for ch in ["all", "vk", "max", "whatsapp", "telegram_bot"]:
            t0 = time.time()
            res = db.exec(text(sql), params={"channel": ch}).all()
            t1 = time.time()
            print(f"Канал '{ch}': {len(res)} диалогов найдено за {t1 - t0:.4f} сек")

if __name__ == "__main__":
    test_fast_filter()
