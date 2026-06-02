import logging
import asyncio
from typing import Dict, Any, Optional, List
from sqlmodel import Session, select
from app.core.database import engine
from app.models.order import Order, OrderStatus
from app.models.mailing_cascade import MailingCascade, MailingCascadeStep
from datetime import datetime, timezone

logger = logging.getLogger(__name__)

class MailingCascadeService:
    async def trigger_cascade(self, order: Order, event_type: str):
        """
        Запуск каскада уведомлений для события.
        """
        try:
            with Session(engine) as session:
                # Ищем активный каскад для этого события
                cascade = session.exec(
                    select(MailingCascade)
                    .where(MailingCascade.trigger_event == event_type)
                    .where(MailingCascade.is_active == True)
                ).first()
                
                if not cascade or not cascade.steps:
                    logger.debug(f"No active cascade for event {event_type}")
                    return

                # Находим первый шаг (с минимальным приоритетом)
                steps = sorted(cascade.steps, key=lambda x: x.priority)
                first_step = steps[0]
                
                logger.info(f"Triggering cascade '{cascade.name}' for order {order.id}, step 1: {first_step.channel}")

                # Если задержка 0 - выполняем сразу
                if first_step.delay_minutes == 0:
                    await self.execute_step(cascade.id, first_step.id, order.id)
                else:
                    # Планируем через Celery
                    from app.tasks.mailing_tasks import execute_cascade_step_task
                    execute_cascade_step_task.apply_async(
                        args=[cascade.id, first_step.id, order.id],
                        countdown=first_step.delay_minutes * 60
                    )
        except Exception as e:
            logger.error(f"Error triggering cascade: {e}")

    async def execute_step(self, cascade_id: int, step_id: int, order_id: int):
        """
        Выполнение конкретного шага каскада.
        """
        try:
            with Session(engine) as session:
                cascade = session.get(MailingCascade, cascade_id)
                step = session.get(MailingCascadeStep, step_id)
                order = session.get(Order, order_id)
                
                if not cascade or not step or not order:
                    logger.warning(f"Cascade execution context missing: cascade={cascade_id}, step={step_id}, order={order_id}")
                    return

                # 1. Проверяем условия (condition)
                # currently supported: always
                # TODO: add logic for if_previous_failed, etc.
                
                # 2. Рендерим шаблон
                message = self.render_template(step.template, order)

                # 3. Отправляем в зависимости от канала
                success = False
                if step.channel == "vk":
                    success = await self.send_vk(order, message, session)
                elif step.channel == "max":
                    success = await self.send_max(order, message, session)
                elif step.channel == "telegram":
                    success = await self.send_telegram(order, message, session)
                
                logger.info(f"Cascade step {step.id} ({step.channel}) for order {order.id}: success={success}")

                # 4. Переходим к следующему шагу
                next_step = session.exec(
                    select(MailingCascadeStep)
                    .where(MailingCascadeStep.cascade_id == cascade_id)
                    .where(MailingCascadeStep.priority > step.priority)
                    .order_by(MailingCascadeStep.priority)
                ).first()

                if next_step:
                    # Планируем следующий шаг
                    from app.tasks.mailing_tasks import execute_cascade_step_task
                    execute_cascade_step_task.apply_async(
                        args=[cascade.id, next_step.id, order.id],
                        countdown=next_step.delay_minutes * 60
                    )
        except Exception as e:
            logger.error(f"Error executing cascade step: {e}")

    def render_template(self, template: str, order: Order) -> str:
        """Подстановка переменных в шаблон сообщения"""
        # Состав заказа
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

        variables = {
            "{order_number}": order.external_number or str(order.id),
            "{order_type}": order.order_type or "Заказ",
            "{address}": order.delivery_address or "---",
            "{customer_name}": order.customer_name or "Гость",
            "{items}": items_text,
            "{total_sum}": f"{float(order.total_with_discount or 0):.0f}",
            "{status}": status_names.get(order.status, "Обработан")
        }

        message = template
        for var, value in variables.items():
            message = message.replace(var, str(value))
        return message

    async def send_vk(self, order: Order, message: str, session: Session) -> bool:
        """Отправка сообщения через VK"""
        from app.models.vk_settings import VkSettings
        from app.models.vk_user import VkUser
        from app.models.customer import Customer
        from app.services.vk_service import send_vk_message
        
        vk_settings = session.exec(select(VkSettings)).first()
        if not vk_settings or not vk_settings.vk_bot_token:
            return False

        vk_id = None
        if order.customer_id:
            customer = session.get(Customer, order.customer_id)
            if customer and customer.vk_user_id:
                vk_id = customer.vk_user_id
        
        if not vk_id and order.customer_phone:
            vk_user = session.exec(select(VkUser).where(VkUser.phone == order.customer_phone)).first()
            if vk_user and vk_user.is_linked:
                vk_id = vk_user.vk_id

        if not vk_id:
            return False

        return await send_vk_message(vk_id, message, vk_settings.vk_bot_token)

    async def send_max(self, order: Order, message: str, session: Session) -> bool:
        """Отправка сообщения через MAX Messenger"""
        from app.models.max_settings import MaxSettings
        from app.services.max_service import send_max_message
        
        settings = session.exec(select(MaxSettings)).first()
        if not settings or not settings.is_active:
            logger.warning("MAX settings not found or not active")
            return False

        if not order.customer_phone:
            logger.warning(f"No phone for order {order.id}, skipping MAX")
            return False

        return await send_max_message(order.customer_phone, message, settings)

    async def send_telegram(self, order: Order, message: str, session: Session) -> bool:
        """Отправка сообщения через Telegram Бота"""
        # Пока заглушка
        logger.warning(f"Telegram integration called for order {order.id} but not fully implemented. Msg: {message}")
        return False

mailing_cascade_service = MailingCascadeService()
