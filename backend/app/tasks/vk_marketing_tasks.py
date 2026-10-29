import logging
import asyncio
from datetime import datetime, timedelta
from celery import shared_task
from sqlmodel import Session, select, text
from app.core.database import SessionLocal
from app.models.order import Order
from app.models.customer import Customer
from app.models.vk_bot_connection import VkBotConnection
from app.services.vk_service import send_vk_message

logger = logging.getLogger(__name__)


def _run_async(coro):
    """Хелпер для запуска асинхронных корутин внутри синхронных Celery воркеров"""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop.run_until_complete(coro)


@shared_task(name="app.tasks.vk_marketing_tasks.task_vk_nps_survey")
def task_vk_nps_survey():
    """
    Периодическая задача опроса NPS (каждые 5-15 минут):
    Ищет доставленные заказы, по которым еще не отправлялся опрос.
    """
    with SessionLocal() as db:
        # Проверяем активные боты NPS
        bots = db.execute(text("SELECT * FROM vk_review_nps_bots WHERE is_active = true")).mappings().all()
        if not bots:
            return "No active NPS bots"

        for bot_cfg in bots:
            conn_id = bot_cfg["vk_bot_connection_id"]
            conn = db.get(VkBotConnection, conn_id)
            if not conn or not (conn.vk_bot_token or conn.bot_token):
                continue

            bot_token = conn.vk_bot_token or conn.bot_token
            delay_min = int(bot_cfg.get("delay_minutes_after_delivery", 45) or 45)
            min_sum = float(bot_cfg.get("min_order_amount_for_nps", 500) or 500)

            # Ищем заказы, доставленные от delay_min до delay_min + 120 минут назад
            orders = db.execute(text(f"""
                SELECT o.id, o.external_number, o.customer_id, o.total_amount, c.vk_user_id, c.first_name, c.name
                FROM orders o
                JOIN customers c ON c.id = o.customer_id
                LEFT JOIN vk_order_nps_reviews r ON r.order_id = o.id
                WHERE o.status IN ('Delivered', 'Closed', 'completed')
                  AND o.created_at <= NOW() - INTERVAL '{delay_min} minutes'
                  AND o.created_at >= NOW() - INTERVAL '{delay_min + 180} minutes'
                  AND COALESCE(o.total_amount, 0) >= {min_sum}
                  AND c.vk_user_id IS NOT NULL
                  AND r.id IS NULL
                LIMIT 20
            """)).mappings().all()

            for ord_row in orders:
                vk_id = ord_row["vk_user_id"]
                num = ord_row["external_number"] or ord_row["id"]
                fname = ord_row["first_name"] or ord_row["name"] or "друг"

                template = bot_cfg.get("msg_ask_rating") or "Ваш заказ №{order_number} доставлен! Оцените, пожалуйста, блюда и доставку от 1 до 5:"
                msg_text = template.replace("{order_number}", str(num)).replace("{first_name}", fname)

                keyboard = {
                    "inline": True,
                    "buttons": [[
                        {"action": {"type": "text", "label": "⭐ 1", "payload": f"{{\"cmd\":\"nps_rate\",\"order_id\":{ord_row['id']},\"rate\":1}}"}, "color": "negative"},
                        {"action": {"type": "text", "label": "⭐ 2", "payload": f"{{\"cmd\":\"nps_rate\",\"order_id\":{ord_row['id']},\"rate\":2}}"}, "color": "negative"},
                        {"action": {"type": "text", "label": "⭐ 3", "payload": f"{{\"cmd\":\"nps_rate\",\"order_id\":{ord_row['id']},\"rate\":3}}"}, "color": "secondary"},
                        {"action": {"type": "text", "label": "⭐ 4", "payload": f"{{\"cmd\":\"nps_rate\",\"order_id\":{ord_row['id']},\"rate\":4}}"}, "color": "positive"},
                        {"action": {"type": "text", "label": "⭐ 5", "payload": f"{{\"cmd\":\"nps_rate\",\"order_id\":{ord_row['id']},\"rate\":5}}"}, "color": "positive"}
                    ]]
                }

                try:
                    _run_async(send_vk_message(
                        vk_id=int(vk_id),
                        message=msg_text,
                        bot_token=bot_token,
                        keyboard=keyboard
                    ))
                    # Записываем пустышку в vk_order_nps_reviews с rating=0 (ожидание оценки)
                    db.execute(text(f"""
                        INSERT INTO vk_order_nps_reviews (order_id, vk_id, rating, created_at)
                        VALUES ({ord_row['id']}, {vk_id}, 0, NOW())
                        ON CONFLICT DO NOTHING;
                    """))
                    db.commit()
                except Exception as e:
                    logger.error(f"Error sending NPS survey to VK ID {vk_id}: {e}")

    return "NPS survey task completed"


@shared_task(name="app.tasks.vk_marketing_tasks.task_vk_wheel_reminders")
def task_vk_wheel_reminders():
    """
    Напоминание о сгорании неиспользованных выигрышей в Колесе Фортуны
    """
    with SessionLocal() as db:
        spins = db.execute(text("""
            SELECT s.id, s.vk_id, s.prize_name, s.promo_code, b.vk_bot_connection_id
            FROM vk_wheel_spins s
            JOIN vk_wheel_bots b ON b.id = s.wheel_bot_id
            WHERE s.is_used = false
              AND s.expires_at BETWEEN NOW() AND NOW() + INTERVAL '24 hours'
            LIMIT 30
        """)).mappings().all()

        for spin in spins:
            conn = db.get(VkBotConnection, spin["vk_bot_connection_id"])
            if not conn:
                continue
            token = conn.vk_bot_token or conn.bot_token
            if not token:
                continue

            msg = f"⏰ Напоминаем! Ваш выигрыш «{spin['prize_name']}» по промокоду {spin['promo_code']} сгорит через 24 часа! Успейте сделать заказ на vezuroll.ru!"
            try:
                _run_async(send_vk_message(vk_id=int(spin["vk_id"]), message=msg, bot_token=token))
            except Exception as e:
                logger.warning(f"Error sending wheel reminder: {e}")

    return "Wheel reminders task completed"
