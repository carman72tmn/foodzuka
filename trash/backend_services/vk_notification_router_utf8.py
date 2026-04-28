import logging
from typing import Optional, Dict, Any, List
from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_bot import VkBotAccount, VkBotSubscription, VkBotMessageLog, DeliveryMode, MessageStatus
from app.services.vk_bot_service import vk_bot_service

logger = logging.getLogger(__name__)

class VkNotificationRouter:
    """Маршрутизатор уведомлений для VK Бота"""

    async def dispatch_event(self, event_type: str, message_text: str, context_data: Optional[Dict[str, Any]] = None):
        """
        Основной метод для отправки системного события.
        Находит всех активных подписчиков и распределяет сообщения.
        """
        logger.info(f"Dispatching VK event: {event_type}")
        
        with Session(engine) as session:
            from app.models.vk_bot import VkTemplate
            
            # 1. Пытаемся найти шаблон для этого события
            template = session.exec(select(VkTemplate).where(VkTemplate.name == event_type)).first()
            
            final_text = message_text
            keyboard = None
            
            if template:
                final_text = template.text
                keyboard = template.keyboard_json
                
                # Рендерим переменные, если есть контекст
                if context_data:
                    try:
                        # Простая реализация замены {{ key.path }}
                        for key, value in context_data.items():
                            if isinstance(value, dict):
                                for sub_key, sub_value in value.items():
                                    placeholder = "{{" + f" {key}.{sub_key} " + "}}"
                                    placeholder_no_spaces = "{{" + f"{key}.{sub_key}" + "}}"
                                    final_text = final_text.replace(placeholder, str(sub_value))
                                    final_text = final_text.replace(placeholder_no_spaces, str(sub_value))
                            else:
                                placeholder = "{{" + f" {key} " + "}}"
                                placeholder_no_spaces = "{{" + f"{key}" + "}}"
                                final_text = final_text.replace(placeholder, str(value))
                                final_text = final_text.replace(placeholder_no_spaces, str(value))
                    except Exception as e:
                        logger.error(f"Error rendering template {event_type}: {e}")

            # 2. Ищем подписки на это событие
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
                # Проверяем, подписан ли аккаунт на этот тип события
                # Если enabled_events пуст, значит подписан на всё (для обратной совместимости)
                if account.enabled_events and len(account.enabled_events) > 0:
                    if event_type not in account.enabled_events:
                        continue

                # Фильтрация для курьеров: если событие courier_assigned, 
                # отправляем только тому, чье employee_id совпадает с назначенным
                if event_type == "courier_assigned" and context_data and "courier_employee_id" in context_data:
                    if account.employee_id != context_data["courier_employee_id"]:
                        continue

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
                        message=final_text,
                        account_id=account.id,
                        event_type=event_type,
                        keyboard=keyboard
                    )
                else:
                    # Сохраняем в очередь для дайджеста
                    log_entry = VkBotMessageLog(
                        account_id=account.id,
                        text=final_text,
                        event_type=event_type,
                        status=MessageStatus.PENDING
                    )
                    session.add(log_entry)
            
            session.commit()

    async def send_manual_broadcast(self, text: str, account_ids: List[int] = None, group_ids: List[int] = None, keyboard: Optional[str] = None):
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
                    event_type="manual_broadcast",
                    keyboard=keyboard
                )

vk_notification_router = VkNotificationRouter()
