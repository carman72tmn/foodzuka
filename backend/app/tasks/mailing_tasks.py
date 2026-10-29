import asyncio
import logging
from app.core.celery_app import celery_app
from app.services.mailing_cascade_service import mailing_cascade_service
from typing import Optional

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.mailing_tasks.execute_cascade_step_task")
def execute_cascade_step_task(
    self, 
    cascade_id: int, 
    step_id: int, 
    customer_id: int,
    order_id: Optional[int] = None,
    broadcast_id: Optional[int] = None,
    reminder_id: Optional[int] = None
):
    """
    Задача выполнения шага каскада рассылки.
    """
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        # Запускаем асинхронный метод через event loop
        loop.run_until_complete(
            mailing_cascade_service.execute_step(
                cascade_id=cascade_id,
                step_id=step_id,
                customer_id=customer_id,
                order_id=order_id,
                broadcast_id=broadcast_id,
                reminder_id=reminder_id
            )
        )
        return {"status": "success", "step_id": step_id, "customer_id": customer_id}
    except Exception as e:
        logger.error(f"Error in execute_cascade_step_task: {e}")
        raise e

@celery_app.task(bind=True, name="app.tasks.mailing_tasks.execute_customer_broadcast_task")
def execute_customer_broadcast_task(self, broadcast_id: int):
    """
    Задача фонового выполнения рассылки клиентам.
    """
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(
            run_customer_broadcast(broadcast_id)
        )
        return {"status": "success", "broadcast_id": broadcast_id}
    except Exception as e:
        logger.error(f"Error in execute_customer_broadcast_task: {e}")
        raise e

@celery_app.task(bind=True, name="app.tasks.mailing_tasks.send_inactive_customer_reminders_task")
def send_inactive_customer_reminders_task(self):
    """
    Периодическая задача ежедневной проверки неактивных клиентов и отправки напоминаний.
    """
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(
            run_inactive_customer_reminders()
        )
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Error in send_inactive_customer_reminders_task: {e}")
        raise e


async def run_customer_broadcast(broadcast_id: int):
    from sqlmodel import Session, select
    from app.core.database import engine
    from app.models.customer import Customer
    from app.models.broadcast import CustomerBroadcast
    from datetime import datetime, timezone, timedelta
    
    with Session(engine) as session:
        broadcast = session.get(CustomerBroadcast, broadcast_id)
        if not broadcast or broadcast.status not in ("draft", "scheduled"):
            logger.warning(f"Broadcast {broadcast_id} not found or not in draft/scheduled status")
            return
            
        broadcast.status = "processing"
        session.add(broadcast)
        session.commit()
        
        # Строим фильтры целевой аудитории
        query = select(Customer).where(Customer.is_blocked == False)
        filters = broadcast.audience_filters or {}
        
        # 1. По неактивности
        if "days_inactive" in filters and filters["days_inactive"]:
            D = int(filters["days_inactive"])
            threshold = datetime.now(timezone.utc) - timedelta(days=D)
            query = query.where(Customer.last_order_date <= threshold)
            
        # 2. По сумме заказов (LTV)
        if "total_orders_amount_min" in filters and filters["total_orders_amount_min"]:
            min_spent = float(filters["total_orders_amount_min"])
            query = query.where(Customer.total_orders_amount >= min_spent)
            
        # 3. По количеству заказов
        if "total_orders_count_min" in filters and filters["total_orders_count_min"]:
            min_count = int(filters["total_orders_count_min"])
            query = query.where(Customer.total_orders_count >= min_count)
            
        customers = session.exec(query).all()
        logger.info(f"Starting broadcast {broadcast_id} to {len(customers)} customers")
        
        # Запускаем каскады с паузой
        for idx, customer in enumerate(customers):
            await mailing_cascade_service.trigger_cascade(
                customer_id=customer.id,
                event_type="broadcast",
                broadcast_id=broadcast_id
            )
            # Небольшая пауза во избежание перегрузки воркера и API
            if idx % 5 == 0:
                await asyncio.sleep(0.5)
                
        broadcast.status = "completed"
        broadcast.updated_at = datetime.now(timezone.utc)
        session.add(broadcast)
        session.commit()
        logger.info(f"Broadcast {broadcast_id} successfully started for all target customers")


async def run_inactive_customer_reminders():
    from sqlmodel import Session, select
    from app.core.database import engine
    from app.models.customer import Customer
    from app.models.reminder import CustomerReminder, SentReminder
    from datetime import datetime, timezone, timedelta
    
    with Session(engine) as session:
        # Ищем все активные правила напоминаний
        reminders = session.exec(select(CustomerReminder).where(CustomerReminder.is_active == True)).all()
        if not reminders:
            logger.info("No active customer reminders configured")
            return
            
        for reminder in reminders:
            # Нам нужно найти клиентов, у которых последний заказ был ровно D дней назад
            D = reminder.days_inactive
            
            # Определяем интервал для last_order_date
            today = datetime.now(timezone.utc).date()
            target_date = today - timedelta(days=D)
            
            # Ищем клиентов, у которых last_order_date приходится на target_date
            from sqlalchemy import cast, Date
            query = select(Customer).where(
                Customer.is_blocked == False,
                Customer.last_order_date != None,
                cast(Customer.last_order_date, Date) == target_date
            )
            
            customers = session.exec(query).all()
            logger.info(f"Reminder rule '{reminder.name}' (ID: {reminder.id}) targets {len(customers)} customers (last order date: {target_date})")
            
            for customer in customers:
                # Проверяем, не отправляли ли уже это напоминание клиенту
                already_sent = session.exec(
                    select(SentReminder).where(
                        SentReminder.reminder_id == reminder.id,
                        SentReminder.customer_id == customer.id
                    )
                ).first()
                
                if already_sent:
                    continue
                    
                # Логируем отправку и запускаем каскад
                sent_log = SentReminder(
                    reminder_id=reminder.id,
                    customer_id=customer.id,
                    sent_at=datetime.now(timezone.utc)
                )
                session.add(sent_log)
                session.commit()
                
                await mailing_cascade_service.trigger_cascade(
                    customer_id=customer.id,
                    event_type="reminder",
                    reminder_id=reminder.id
                )
                await asyncio.sleep(0.1)


async def delete_shared_payment_qrs(order_id: int):
    from sqlmodel import Session, select
    from app.core.database import engine
    from app.models.vk_bot import OrderPaymentQrShare
    from app.services.vk_bot_service import vk_bot_service
    from app.services.vk_notification_router import get_telegram_token
    import httpx
    
    with Session(engine) as session:
        shares = session.exec(select(OrderPaymentQrShare).where(OrderPaymentQrShare.order_id == order_id)).all()
        if not shares:
            return
            
        vk_token = vk_bot_service._get_bot_token()
        tg_token = get_telegram_token(session)
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            for share in shares:
                try:
                    if share.channel == "vk" and vk_token:
                        url = "https://api.vk.ru/method/messages.delete"
                        params = {
                            "access_token": vk_token,
                            "v": "5.131",
                            "message_ids": int(share.message_id),
                            "delete_for_all": 1
                        }
                        res = await client.post(url, data=params)
                        logger.info(f"VK message delete response for order {order_id}: {res.json()}")
                    elif (share.channel == "tg" or share.channel == "telegram") and tg_token:
                        url = f"https://api.telegram.org/bot{tg_token}/deleteMessage"
                        payload = {
                            "chat_id": int(share.chat_id),
                            "message_id": int(share.message_id)
                        }
                        res = await client.post(url, json=payload)
                        logger.info(f"Telegram message delete response for order {order_id}: {res.json()}")
                    
                    # Удаляем запись из БД после попытки удаления
                    session.delete(share)
                except Exception as e:
                    logger.error(f"Error deleting shared QR code message in channel {share.channel}: {e}")
                    
        session.commit()


@celery_app.task(bind=True, name="app.tasks.mailing_tasks.delete_shared_payment_qrs_task")
def delete_shared_payment_qrs_task(self, order_id: int):
    """
    Задача удаления отправленных QR-кодов оплаты из чатов после успешного платежа.
    """
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(
            delete_shared_payment_qrs(order_id)
        )
        return {"status": "success", "order_id": order_id}
    except Exception as e:
        logger.error(f"Error in delete_shared_payment_qrs_task: {e}")
        raise e
