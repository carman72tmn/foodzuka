import logging
from typing import Optional, Dict, Any, List
from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_bot import VkBotAccount, VkBotSubscription, VkBotMessageLog, DeliveryMode, MessageStatus
from app.services.vk_bot_service import vk_bot_service

logger = logging.getLogger(__name__)

class VkNotificationRouter:
    """Маршрутизатор уведомлений для VK Бота"""

    async def dispatch_event(self, event_type: str, message_text: str, **kwargs):
        """
        Основной метод для отправки системного события.
        Находит всех активных подписчиков и распределяет сообщения.
        """
        logger.info(f"Dispatching VK event: {event_type}")
        
        with Session(engine) as session:
            # Ищем подписки на это событие
            statement = (
                select(VkBotSubscription, VkBotAccount)
                .join(VkBotAccount)
                .where(VkBotSubscription.event_type == event_type)
                .where(VkBotAccount.is_active == True)
                .where(VkBotAccount.is_verified == True)
            )
            results = session.exec(statement).all()

            from app.core.datetime_utils import get_tz_name, get_local_now
            current_hour = get_local_now(get_tz_name(session)).hour

            for sub, account in results:
                # Проверка диапазона активности
                is_active_hour = False
                if sub.active_start_hour <= sub.active_end_hour:
                    is_active_hour = sub.active_start_hour <= current_hour <= sub.active_end_hour
                else:
                    # Переход через полночь (например, с 22 до 06)
                    is_active_hour = current_hour >= sub.active_start_hour or current_hour <= sub.active_end_hour

                if not is_active_hour:
                    logger.debug(f"Skipping notification for {account.name}: outside active hours ({sub.active_start_hour}-{sub.active_end_hour})")
                    continue

                if sub.delivery_mode == DeliveryMode.REALTIME:
                    # Отправляем немедленно
                    await vk_bot_service.send_message(
                        user_id=account.vk_user_id,
                        message=message_text,
                        account_id=account.id,
                        event_type=event_type
                    )
                else:
                    # Сохраняем в очередь для дайджеста
                    log_entry = VkBotMessageLog(
                        account_id=account.id,
                        text=message_text,
                        event_type=event_type,
                        status=MessageStatus.PENDING
                    )
                    session.add(log_entry)
            
            session.commit()

    async def send_manual_broadcast(self, text: str, account_ids: List[int] = None, group_ids: List[int] = None):
        """
        Ручная рассылка сообщения выбранным аккаунтам или группам.
        """
        with Session(engine) as session:
            # Собираем всех получателей
            recipients = []
            
            if account_ids:
                recipients.extend(session.exec(select(VkBotAccount).where(VkBotAccount.id.in_(account_ids))).all())
            
            if group_ids:
                # Тут логика с группами (нужно подтянуть аккаунты из групп)
                from app.models.vk_bot import VkBotAccountGroupLink
                stmt = (
                    select(VkBotAccount)
                    .join(VkBotAccountGroupLink)
                    .where(VkBotAccountGroupLink.group_id.in_(group_ids))
                    .where(VkBotAccount.is_active == True)
                )
                recipients.extend(session.exec(stmt).all())

            # Убираем дубликаты по vk_user_id
            unique_recipients = {acc.vk_user_id: acc for acc in recipients}.values()

            for account in unique_recipients:
                await vk_bot_service.send_message(
                    user_id=account.vk_user_id,
                    message=text,
                    account_id=account.id,
                    event_type="manual_broadcast"
                )

vk_notification_router = VkNotificationRouter()
