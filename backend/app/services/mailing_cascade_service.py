import logging
import asyncio
import os
import re
import random
import string
from typing import Dict, Any, Optional, List
from sqlmodel import Session, select
from app.core.database import engine
from app.models.customer import Customer
from app.models.order import Order, OrderStatus
from app.models.mailing_cascade import MailingCascade, MailingCascadeStep
from app.models.message_log import CustomerMessageLog, ShortLink
from app.models.broadcast import CustomerBroadcast
from app.models.reminder import CustomerReminder
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MailingCascadeService:
    async def trigger_cascade(
        self, 
        customer_id: int, 
        event_type: str, 
        order_id: Optional[int] = None,
        broadcast_id: Optional[int] = None,
        reminder_id: Optional[int] = None,
        cascade_id: Optional[int] = None
    ):
        """
        Запуск каскада уведомлений для события и гостя.
        """
        try:
            with Session(engine) as session:
                # Совместимость: если вместо ID клиента передан объект Order
                from app.models.order import Order
                order = None
                if isinstance(customer_id, Order):
                    order = customer_id
                    order_id = order.id
                    customer_id = order.customer_id
                elif order_id:
                    order = session.get(Order, order_id)

                # Фоллбэк: если customer_id не задан, но есть заказ с телефоном
                if not customer_id and order and order.customer_phone:
                    from app.models.customer import Customer
                    customer_obj = session.exec(select(Customer).where(Customer.phone == order.customer_phone)).first()
                    if customer_obj:
                        customer_id = customer_obj.id
                        if order.customer_id != customer_obj.id:
                            order.customer_id = customer_obj.id
                            session.add(order)
                            session.commit()

                # Адаптация event_type на основе статуса заказа для детальных триггеров
                if order:
                    from app.models.order import OrderStatus
                    status_event_map = {
                        OrderStatus.new: "new_order",
                        OrderStatus.confirmed: "order_confirmed",
                        OrderStatus.cooking: "order_cooking",
                        OrderStatus.ready: "order_ready",
                        OrderStatus.ready_for_pickup: "order_ready_for_pickup",
                        OrderStatus.delivering: "order_delivering",
                        OrderStatus.delivered: "order_delivered",
                        OrderStatus.closed: "order_closed",
                        OrderStatus.cancelled: "order_cancelled"
                    }
                    if event_type in ("order_status_update", "order_new", "new_order"):
                        if order.status in status_event_map:
                            old_event = event_type
                            event_type = status_event_map[order.status]
                            logger.info(f"Adapted event_type from '{old_event}' to '{event_type}' for order {order.id} status '{order.status}'")

                cascade = None
                # Если передан cascade_id напрямую, используем его
                if cascade_id:
                    cascade = session.get(MailingCascade, cascade_id)
                
                # Если cascade_id не передан напрямую, пытаемся найти его в напоминании или рассылке
                if not cascade:
                    if reminder_id:
                        reminder = session.get(CustomerReminder, reminder_id)
                        if reminder and reminder.cascade_id:
                            cascade = session.get(MailingCascade, reminder.cascade_id)
                    elif broadcast_id:
                        broadcast = session.get(CustomerBroadcast, broadcast_id)
                        if broadcast and broadcast.cascade_id:
                            cascade = session.get(MailingCascade, broadcast.cascade_id)

                # Если все еще не нашли, ищем по триггеру (event_type)
                if not cascade:
                    statement = select(MailingCascade).where(
                        MailingCascade.trigger_event == event_type,
                        MailingCascade.is_active == True
                    )
                    
                    # Если это системный статус заказа, фильтруем по типу доставки
                    if order:
                        if order.order_type:
                            order_type_mapped = "delivery" if order.order_type == "Доставка" else "pickup"
                            statement = statement.where(
                                (MailingCascade.order_type == order_type_mapped) | 
                                (MailingCascade.order_type == "any") | 
                                (MailingCascade.order_type == None)
                            )
                    
                    cascade = session.exec(statement.order_by(MailingCascade.id.desc())).first()

                    # Фоллбэк: если точного совпадения нет, а событие - готовность самовывоза,
                    # то пробуем найти общий триггер "Заказ готов" (order_ready)
                    if not cascade and event_type == "order_ready_for_pickup":
                        logger.info(f"Cascade for 'order_ready_for_pickup' not found, trying fallback to 'order_ready'")
                        fallback_statement = select(MailingCascade).where(
                            MailingCascade.trigger_event == "order_ready",
                            MailingCascade.is_active == True
                        )
                        if order and order.order_type:
                            order_type_mapped = "delivery" if order.order_type == "Доставка" else "pickup"
                            fallback_statement = fallback_statement.where(
                                (MailingCascade.order_type == order_type_mapped) | 
                                (MailingCascade.order_type == "any") | 
                                (MailingCascade.order_type == None)
                            )
                        cascade = session.exec(fallback_statement.order_by(MailingCascade.id.desc())).first()
                
                if not cascade and event_type in ("broadcast", "reminder"):
                    fallback_any = select(MailingCascade).where(MailingCascade.is_active == True).order_by(MailingCascade.id.asc())
                    cascade = session.exec(fallback_any).first()
                    if cascade:
                        logger.info(f"Fallback active cascade #{cascade.id} ('{cascade.name}') used for event '{event_type}'")

                if not cascade or not cascade.steps:
                    logger.debug(f"No active cascade found (event: {event_type}, cascade_id: {cascade_id}, customer: {customer_id})")
                    return

                # Находим первый шаг (с минимальным приоритетом)
                steps = sorted(cascade.steps, key=lambda x: x.priority)
                first_step = steps[0]
                
                logger.info(f"Triggering cascade '{cascade.name}' (ID: {cascade.id}) for customer {customer_id}, step 1: {first_step.channel}")

                # Если задержка 0 - выполняем сразу
                if first_step.delay_minutes == 0:
                    await self.execute_step(
                        cascade.id, 
                        first_step.id, 
                        customer_id, 
                        order_id, 
                        broadcast_id, 
                        reminder_id
                    )
                else:
                    # Планируем через Celery
                    from app.tasks.mailing_tasks import execute_cascade_step_task
                    execute_cascade_step_task.apply_async(
                        args=[cascade.id, first_step.id, customer_id, order_id, broadcast_id, reminder_id],
                        countdown=first_step.delay_minutes * 60
                    )
        except Exception as e:
            logger.error(f"Error triggering cascade: {e}", exc_info=True)

    async def execute_step(
        self, 
        cascade_id: int, 
        step_id: int, 
        customer_id: int,
        order_id: Optional[int] = None,
        broadcast_id: Optional[int] = None,
        reminder_id: Optional[int] = None
    ):
        """
        Выполнение конкретного шага каскада.
        """
        try:
            with Session(engine) as session:
                cascade = session.get(MailingCascade, cascade_id)
                step = session.get(MailingCascadeStep, step_id)
                customer = session.get(Customer, customer_id)
                order = session.get(Order, order_id) if order_id else None
                broadcast = session.get(CustomerBroadcast, broadcast_id) if broadcast_id else None
                reminder = session.get(CustomerReminder, reminder_id) if reminder_id else None
                
                if not cascade or not step or not customer:
                    logger.warning(f"Cascade execution context missing: cascade={cascade_id}, step={step_id}, customer={customer_id}")
                    return

                # Проверка наличия привязанных соцсетей (VK, Telegram, MAX) по номеру телефона / полям
                from app.models.vk_user import VkUser
                has_vk = False
                vk_user_pre = None
                if customer.vk_user_id:
                    vk_user_pre = session.exec(select(VkUser).where(VkUser.vk_id == customer.vk_user_id)).first()
                    if vk_user_pre and vk_user_pre.is_linked:
                        has_vk = True
                if not vk_user_pre and customer.phone:
                    vk_user_pre = session.exec(select(VkUser).where(
                        VkUser.phone == customer.phone,
                        VkUser.is_linked == True
                    )).first()
                    if vk_user_pre:
                        has_vk = True

                has_tg = bool(customer.telegram_id)
                has_max = bool(customer.max_user_id or customer.phone)

                # Все каскады и рассылки идут строго клиентам с привязанными соцсетями
                if not (has_vk or has_tg or has_max):
                    logger.info(f"Skipping cascade step: customer {customer_id} has no linked social accounts")
                    return

                # 1. Проверяем условия выполнения шага (condition)
                if step.priority > 0:
                    # Получаем лог предыдущего шага каскада для этого же заказа/рассылки/напоминания
                    prev_step_stmt = select(MailingCascadeStep).where(
                        MailingCascadeStep.cascade_id == cascade_id,
                        MailingCascadeStep.priority < step.priority
                    ).order_by(MailingCascadeStep.priority.desc())
                    prev_step = session.exec(prev_step_stmt).first()
                    
                    if prev_step:
                        # Ищем лог отправки предыдущего шага
                        log_stmt = select(CustomerMessageLog).where(
                            CustomerMessageLog.customer_id == customer_id,
                            CustomerMessageLog.cascade_step_id == prev_step.id
                        )
                        if order_id: log_stmt = log_stmt.where(CustomerMessageLog.order_id == order_id)
                        if broadcast_id: log_stmt = log_stmt.where(CustomerMessageLog.broadcast_id == broadcast_id)
                        if reminder_id: log_stmt = log_stmt.where(CustomerMessageLog.reminder_id == reminder_id)
                        
                        prev_log = session.exec(log_stmt.order_by(CustomerMessageLog.id.desc())).first()
                        
                        if prev_log:
                            if step.condition == "if_previous_failed" and prev_log.status != "failed":
                                logger.info(f"Skipping step {step_id}: previous step succeeded, but condition is if_previous_failed")
                                return
                            if step.condition == "if_not_read_previous" and prev_log.status in ("read", "clicked"):
                                logger.info(f"Skipping step {step_id}: previous step was read/clicked, but condition is if_not_read_previous")
                                return
                                
                # 2. Рендерим шаблон
                message_text = self.render_template(step.template, customer, order, broadcast, reminder)

                # 3. Создаем запись лога отправки в статусе pending для получения ID (нужно для коротких ссылок)
                recipient_address = ""
                if step.channel == "vk":
                    if not has_vk:
                        logger.info(f"Skipping VK step: customer {customer_id} has no linked VK account")
                        log_entry = CustomerMessageLog(
                            customer_id=customer_id,
                            order_id=order_id,
                            broadcast_id=broadcast_id,
                            reminder_id=reminder_id,
                            cascade_step_id=step.id,
                            channel=step.channel,
                            recipient_address="",
                            text=message_text,
                            status="failed",
                            error_text="VK account not linked",
                            sent_at=datetime.now(timezone.utc)
                        )
                        session.add(log_entry)
                        session.commit()
                        self.schedule_next_step(session, cascade_id, step.priority, customer_id, order_id, broadcast_id, reminder_id)
                        return
                    recipient_address = str(vk_user_pre.vk_id if vk_user_pre else customer.vk_user_id)
                elif step.channel == "telegram":
                    if not has_tg:
                        logger.info(f"Skipping Telegram step: customer {customer_id} has no linked Telegram account")
                        log_entry = CustomerMessageLog(
                            customer_id=customer_id,
                            order_id=order_id,
                            broadcast_id=broadcast_id,
                            reminder_id=reminder_id,
                            cascade_step_id=step.id,
                            channel=step.channel,
                            recipient_address="",
                            text=message_text,
                            status="failed",
                            error_text="Telegram account not linked",
                            sent_at=datetime.now(timezone.utc)
                        )
                        session.add(log_entry)
                        session.commit()
                        self.schedule_next_step(session, cascade_id, step.priority, customer_id, order_id, broadcast_id, reminder_id)
                        return
                    recipient_address = str(customer.telegram_id)
                elif step.channel == "max":
                    if not has_max:
                        logger.info(f"Skipping MAX step: customer {customer_id} has no linked MAX account or phone")
                        log_entry = CustomerMessageLog(
                            customer_id=customer_id,
                            order_id=order_id,
                            broadcast_id=broadcast_id,
                            reminder_id=reminder_id,
                            cascade_step_id=step.id,
                            channel=step.channel,
                            recipient_address="",
                            text=message_text,
                            status="failed",
                            error_text="MAX account or phone not linked",
                            sent_at=datetime.now(timezone.utc)
                        )
                        session.add(log_entry)
                        session.commit()
                        self.schedule_next_step(session, cascade_id, step.priority, customer_id, order_id, broadcast_id, reminder_id)
                        return
                    recipient_address = customer.max_user_id or customer.phone or ""
                elif step.channel == "sms":
                    recipient_address = customer.phone or ""
                
                log_entry = CustomerMessageLog(
                    customer_id=customer_id,
                    order_id=order_id,
                    broadcast_id=broadcast_id,
                    reminder_id=reminder_id,
                    cascade_step_id=step.id,
                    channel=step.channel,
                    recipient_address=recipient_address,
                    text=message_text,
                    status="pending"
                )
                session.add(log_entry)
                session.commit()
                session.refresh(log_entry)

                # 4. Сокращаем ссылки в тексте сообщения для трекинга переходов
                message_text = self.shorten_links_in_message(message_text, log_entry.id, session)
                log_entry.text = message_text
                session.add(log_entry)
                session.commit()

                # 5. Отправляем в зависимости от канала
                success = False
                msg_id = None
                error_msg = None
                
                # Загружаем настройки ВК и других соцсетей
                from app.models.vk_settings import VkSettings
                from app.models.vk_bot_connection import VkBotConnection
                vk_settings = session.exec(select(VkSettings)).first()

                if step.channel == "vk":
                    # Определяем токен ВК бота
                    bot_token = None
                    # Ищем группу пользователя и профиль
                    from app.models.vk_user import VkUser
                    vk_user = vk_user_pre
                    if not vk_user and customer.vk_user_id:
                        vk_user = session.exec(select(VkUser).where(VkUser.vk_id == customer.vk_user_id)).first()
                    
                    if vk_user and vk_user.vk_group_id:
                        bot = session.exec(select(VkBotConnection).where(
                            VkBotConnection.vk_group_id == vk_user.vk_group_id,
                            VkBotConnection.is_active == True
                        )).first()
                        if bot: bot_token = bot.vk_bot_token
                    
                    if not bot_token:
                        main_bot = session.exec(select(VkBotConnection).where(
                            VkBotConnection.is_main == True,
                            VkBotConnection.is_active == True
                        )).first()
                        if main_bot: bot_token = main_bot.vk_bot_token
                        
                    if not bot_token and vk_settings:
                        bot_token = vk_settings.vk_bot_token
                        
                    # Проверяем разрешения и блокировки в vk_user
                    if vk_user:
                        if vk_user.is_blocked:
                            error_msg = "VK notification blocked by admin"
                            logger.info(f"VK notification to {vk_user.vk_id} blocked by admin")
                        elif not vk_user.notifications_enabled:
                            error_msg = "VK notifications disabled by guest"
                            logger.info(f"VK notification to {vk_user.vk_id} disabled in settings")
                        elif not vk_user.is_subscribed:
                            error_msg = "VK notifications skipped: guest not subscribed to bot"
                            logger.info(f"VK notification to {vk_user.vk_id} skipped: guest is not subscribed to bot")
                            
                    recipient_vk_id = vk_user.vk_id if vk_user else customer.vk_user_id
                    
                    if not recipient_vk_id:
                        error_msg = "VK user ID not linked to customer"
                        
                    if recipient_vk_id and not error_msg:
                        if bot_token:
                            from app.services.vk_service import send_vk_message
                            res = await send_vk_message(
                                vk_id=recipient_vk_id,
                                message=message_text,
                                bot_token=bot_token,
                                image_path=step.image_path,
                                keyboard=step.buttons_json
                            )
                            if res:
                                success = True
                                msg_id = str(res) if res is not True else None
                            else:
                                error_msg = "VK message delivery failed"
                        else:
                            error_msg = "VK Bot Token not configured"
                        
                elif step.channel == "telegram":
                    if customer.telegram_id:
                        # Отправка через Telegram
                        from app.models.bot_settings import BotSettings
                        import httpx
                        
                        bot_settings = session.exec(select(BotSettings)).first()
                        if bot_settings and (not getattr(bot_settings, "is_bot_active", True) or not getattr(bot_settings, "is_client_broadcast_active", True)):
                            token = None
                        else:
                            token = bot_settings.telegram_bot_token if (bot_settings and bot_settings.telegram_bot_token) else os.getenv("TELEGRAM_BOT_TOKEN")
                        
                        if token:
                            # Определение метода API (картинка или текст)
                            if step.image_path:
                                url = f"https://api.telegram.org/bot{token}/sendPhoto"
                                payload = {
                                    "chat_id": customer.telegram_id,
                                    "caption": message_text,
                                    "parse_mode": "HTML"
                                }
                                # Если это URL
                                if step.image_path.startswith("http"):
                                    payload["photo"] = step.image_path
                                    async with httpx.AsyncClient() as client:
                                        res = await client.post(url, json=payload)
                                else:
                                    # Отправка локального файла
                                    if os.path.exists(step.image_path):
                                        with open(step.image_path, "rb") as f:
                                            async with httpx.AsyncClient() as client:
                                                res = await client.post(url, data=payload, files={"photo": f})
                                    else:
                                        # Фолбэк на текст
                                        url_text = f"https://api.telegram.org/bot{token}/sendMessage"
                                        payload_text = {
                                            "chat_id": customer.telegram_id,
                                            "text": message_text,
                                            "parse_mode": "HTML"
                                        }
                                        async with httpx.AsyncClient() as client:
                                            res = await client.post(url_text, json=payload_text)
                            else:
                                url = f"https://api.telegram.org/bot{token}/sendMessage"
                                payload = {
                                    "chat_id": customer.telegram_id,
                                    "text": message_text,
                                    "parse_mode": "HTML"
                                }
                                # Поддержка кнопок
                                if step.buttons_json:
                                    import json
                                    try:
                                        payload["reply_markup"] = json.loads(step.buttons_json)
                                    except:
                                        pass
                                        
                                async with httpx.AsyncClient() as client:
                                    res = await client.post(url, json=payload)
                                    
                            tg_data = res.json()
                            if res.status_code == 200 and tg_data.get("ok"):
                                success = True
                                msg_id = str(tg_data["result"]["message_id"])
                            else:
                                error_msg = tg_data.get("description", "Unknown Telegram error")
                        else:
                            error_msg = "Telegram Bot Token not configured"
                    else:
                        error_msg = "Telegram user ID not linked to customer"
                        
                elif step.channel == "max":
                    # Отправка в MAX
                    from app.services.max_service import send_max_message
                    target = customer.max_user_id or customer.phone
                    if target:
                        bot_id_val = getattr(step, "max_bot_id", None)
                        prefer_mode_val = getattr(step, "max_send_mode", None) or "cascade"
                        res = await send_max_message(
                            recipient=target, 
                            phone=customer.phone,
                            text=message_text, 
                            session=session,
                            bot_id=bot_id_val,
                            prefer_channel=prefer_mode_val
                        )
                        if res and not (isinstance(res, dict) and not res.get("success", False)):
                            success = True
                            msg_id = str(res.get("msg_id") or "")
                        else:
                            error_msg = res.get("error", "MAX Messenger delivery failed") if isinstance(res, dict) else "MAX delivery failed"
                    else:
                        error_msg = "У клиента отсутствует номер телефона или MAX ID"
                        
                elif step.channel == "sms":
                    if customer.phone:
                        # Лог SMS рассылки (SMS-шлюз не подключен, пишем заглушку в логи)
                        logger.info(f"SMS SENT to {customer.phone}: {message_text}")
                        success = True
                    else:
                        error_msg = "Customer phone missing"

                # 6. Обновляем статус лога
                log_entry.status = "sent" if success else "failed"
                log_entry.message_id = msg_id
                log_entry.error_text = error_msg
                log_entry.sent_at = datetime.now(timezone.utc)
                session.add(log_entry)
                session.commit()
                
                # Обновляем метрики в рассылке
                if broadcast_id:
                    broadcast = session.get(CustomerBroadcast, broadcast_id)
                    if broadcast:
                        if success:
                            broadcast.sent_count += 1
                        else:
                            broadcast.error_count += 1
                        session.add(broadcast)
                        session.commit()

                logger.info(f"Cascade step {step.id} ({step.channel}) executed. Success: {success}")

                # 7. Переходим к следующему шагу
                self.schedule_next_step(session, cascade_id, step.priority, customer_id, order_id, broadcast_id, reminder_id)
        except Exception as e:
            logger.error(f"Error executing cascade step: {e}", exc_info=True)

    def schedule_next_step(
        self,
        session: Session,
        cascade_id: int,
        current_priority: int,
        customer_id: int,
        order_id: Optional[int] = None,
        broadcast_id: Optional[int] = None,
        reminder_id: Optional[int] = None
    ):
        """Планирование следующего шага каскада"""
        try:
            next_step = session.exec(
                select(MailingCascadeStep)
                .where(MailingCascadeStep.cascade_id == cascade_id)
                .where(MailingCascadeStep.priority > current_priority)
                .order_by(MailingCascadeStep.priority)
            ).first()

            if next_step:
                from app.tasks.mailing_tasks import execute_cascade_step_task
                execute_cascade_step_task.apply_async(
                    args=[cascade_id, next_step.id, customer_id, order_id, broadcast_id, reminder_id],
                    countdown=next_step.delay_minutes * 60
                )
        except Exception as e:
            logger.error(f"Error executing cascade step: {e}", exc_info=True)

    def render_template(
        self, 
        template: str, 
        customer: Customer, 
        order: Optional[Order] = None,
        broadcast: Optional[CustomerBroadcast] = None,
        reminder: Optional[CustomerReminder] = None
    ) -> str:
        """Подстановка переменных в шаблон сообщения"""
        
        # 1. Извлекаем данные из снимка в заказе (customer_info_details), если заказ передан
        cust_details = {}
        if order and hasattr(order, 'customer_info_details') and order.customer_info_details:
            cust_details = order.customer_info_details
            if not isinstance(cust_details, dict):
                cust_details = {}

        # 2. Вычисляем телефон гостя (сначала из снимка/заказа, потом из объекта customer)
        phone_val = "---"
        if order and hasattr(order, 'customer_phone') and order.customer_phone:
            phone_val = order.customer_phone
        elif cust_details.get("phone"):
            phone_val = cust_details.get("phone")
        elif cust_details.get("customer_phone"):
            phone_val = cust_details.get("customer_phone")
        elif customer and hasattr(customer, 'phone') and customer.phone:
            phone_val = customer.phone

        # 3. Вычисляем баланс бонусов
        bonus_val = 0
        if cust_details.get("bonus_points") is not None:
            bonus_val = cust_details.get("bonus_points")
        elif cust_details.get("bonus_balance") is not None:
            bonus_val = cust_details.get("bonus_balance")
        elif customer and hasattr(customer, 'bonus_points') and customer.bonus_points is not None:
            try:
                bonus_val = float(customer.bonus_points)
                if bonus_val.is_integer():
                    bonus_val = int(bonus_val)
            except:
                bonus_val = customer.bonus_points
        elif customer and hasattr(customer, 'vk_bonus_balance') and customer.vk_bonus_balance is not None:
            bonus_val = customer.vk_bonus_balance
        bonus_str = str(bonus_val)

        # 4. Вычисляем категории клиента
        categories_str = "---"
        cust_categories = cust_details.get("categories") or cust_details.get("iiko_categories")
        if cust_categories:
            if isinstance(cust_categories, list):
                categories_str = ", ".join(cust_categories)
            elif isinstance(cust_categories, str):
                categories_str = cust_categories
        elif customer and hasattr(customer, 'iiko_categories') and customer.iiko_categories:
            if isinstance(customer.iiko_categories, list):
                categories_str = ", ".join(customer.iiko_categories)
            elif isinstance(customer.iiko_categories, str):
                categories_str = customer.iiko_categories

        # 5. Вычисляем заметки о госте
        notes_str = "---"
        cust_notes = cust_details.get("notes") or cust_details.get("iiko_notes")
        if cust_notes:
            notes_str = cust_notes
        elif customer and hasattr(customer, 'notes') and customer.notes:
            notes_str = customer.notes

        # 6. Имя гостя
        name_val = "Гость"
        if order and hasattr(order, 'customer_name') and order.customer_name:
            name_val = order.customer_name
        elif cust_details.get("name"):
            name_val = cust_details.get("name")
        elif customer and hasattr(customer, 'name') and customer.name:
            name_val = customer.name

        # 7. Базовые переменные клиента (Сначала двойные фигурные скобки, затем одинарные!)
        variables = {
            # --- ДВОЙНЫЕ ФИГУРНЫЕ СКОБКИ (Высокий приоритет) ---
            "{{customer_name}}": name_val,
            "{{customer.name}}": name_val,
            "{{customer_phone}}": phone_val,
            "{{customer.phone}}": phone_val,
            "{{bonus_points}}": bonus_str,
            "{{customer.bonus_points}}": bonus_str,
            "{{customer_categories}}": categories_str,
            "{{customer.categories}}": categories_str,
            "{{customer_notes}}": notes_str,
            "{{customer.notes}}": notes_str,
            
            # --- ОДИНАРНЫЕ ФИГУРНЫЕ СКОБКИ (Обычный приоритет) ---
            "{customer_name}": name_val,
            "{customer.name}": name_val,
            "{customer_phone}": phone_val,
            "{customer.phone}": phone_val,
            "{bonus_points}": bonus_str,
            "{customer.bonus_points}": bonus_str,
            "{customer_categories}": categories_str,
            "{customer.categories}": categories_str,
            "{customer_notes}": notes_str,
            "{customer.notes}": notes_str,
        }
        
        # 8. Текст сообщения для рассылки или напоминания
        if reminder:
            variables["{{message_text}}"] = reminder.template
            variables["{message_text}"] = reminder.template
        elif broadcast:
            variables["{{message_text}}"] = broadcast.template_text
            variables["{message_text}"] = broadcast.template_text
            
        # 9. Переменные заказа
        if order:
            items_text = ""
            if order.order_items_details:
                items_list = []
                for item in order.order_items_details:
                    name = item.get("name", "Товар")
                    amount = item.get("amount", 1)
                    items_list.append(f"- {name} x{amount}")
                items_text = "\n".join(items_list)
                
            status_names = {
                OrderStatus.new: "Новый",
                OrderStatus.confirmed: "Подтвержден",
                OrderStatus.cooking: "Готовится",
                OrderStatus.ready: "Готов",
                OrderStatus.ready_for_pickup: "Готов к выдаче",
                OrderStatus.delivering: "В пути",
                OrderStatus.delivered: "Доставлен",
                OrderStatus.closed: "Завершен",
                OrderStatus.cancelled: "Отменен"
            }
            
            order_addr = order.delivery_address or "---"
            order_num = order.external_number or str(order.id)
            
            try:
                total_sum_val = f"{float(order.total_with_discount or 0):.0f}"
            except:
                total_sum_val = str(order.total_with_discount or 0)
                
            status_str = status_names.get(order.status, "Обработан")
            
            # Сначала обновляем двойными скобками
            variables.update({
                "{{address}}": order_addr,
                "{{order.address}}": order_addr,
                "{{order_number}}": order_num,
                "{{order.number}}": order_num,
                "{{items}}": items_text,
                "{{order.items}}": items_text,
                "{{total_sum}}": total_sum_val,
                "{{order.total_sum}}": total_sum_val,
                "{{status}}": status_str,
                "{{order.status}}": status_str,
                "{{order_type}}": order.order_type or "Заказ",
                "{{order.type}}": order.order_type or "Заказ",
            })
            
            # Затем обновляем одинарными скобками
            variables.update({
                "{address}": order_addr,
                "{order.address}": order_addr,
                "{order_number}": order_num,
                "{order.number}": order_num,
                "{items}": items_text,
                "{order.items}": items_text,
                "{total_sum}": total_sum_val,
                "{order.total_sum}": total_sum_val,
                "{status}": status_str,
                "{order.status}": status_str,
                "{order_type}": order.order_type or "Заказ",
                "{order.type}": order.order_type or "Заказ",
            })
            
        message = template
        for var, value in variables.items():
            message = message.replace(var, str(value))
            
        # Повторный прогон для вложенных шаблонов напоминаний/рассылок
        if reminder or broadcast:
            for var, value in variables.items():
                message = message.replace(var, str(value))
                
        return message

    def shorten_links_in_message(self, message: str, message_log_id: int, session: Session) -> str:
        """
        Находит все ссылки в сообщении, создает для них ShortLink 
        и заменяет их на трекинговые короткие ссылки.
        """
        url_pattern = re.compile(r'https?://[^\s<>"]+|www\.[^\s<>"]+')
        urls = url_pattern.findall(message)
        if not urls:
            return message
            
        new_message = message
        for url in urls:
            # Игнорируем ссылки, которые мы уже сократили (содержат /lnk/)
            if "/lnk/" in url:
                continue
                
            # Генерируем уникальный 6-значный код
            while True:
                code = "".join(random.choices(string.ascii_letters + string.digits, k=6))
                existing = session.get(ShortLink, code)
                if not existing:
                    break
            
            # Сохраняем в БД
            short_link = ShortLink(
                code=code,
                message_log_id=message_log_id,
                original_url=url
            )
            session.add(short_link)
            
            # Заменяем в сообщении
            tracking_url = f"https://vezuroll.ru/lnk/{code}"
            new_message = new_message.replace(url, tracking_url)
            
        session.commit()
        return new_message

mailing_cascade_service = MailingCascadeService()
