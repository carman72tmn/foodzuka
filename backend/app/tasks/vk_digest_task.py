import logging
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.models.vk_bot import (
    VkBotAccount, VkBotSubscription, VkBotMessageLog, 
    DeliveryMode, MessageStatus
)
from app.services.vk_bot_service import vk_bot_service
from app.core.datetime_utils import utc_now

logger = logging.getLogger(__name__)

async def process_vk_digests():
    """Задача по рассылке накопленных уведомлений (дайджестов)"""
    logger.info("Starting VK digest processing task...")
    
    with Session(engine) as session:
        # 1. Получаем все подписки с режимом INTERVAL
        # Для SQLModel подтягиваем связанные аккаунты
        subscriptions_with_accs = session.exec(
            select(VkBotSubscription, VkBotAccount)
            .join(VkBotAccount)
            .where(VkBotSubscription.delivery_mode == DeliveryMode.INTERVAL)
            .where(VkBotAccount.is_active == True)
        ).all()
        
        now = utc_now()
        
        for sub, account in subscriptions_with_accs:
            # Проверяем, пришло ли время дайджеста
            # Если last_digest_at нет, отсчитываем от времени создания аккаунта
            last_sent = sub.last_digest_at or account.created_at
            interval = sub.interval_minutes or 60
            
            # Разница в минутах
            time_diff = (now - last_sent).total_seconds() / 60
            
            if time_diff >= interval:
                # 2. Ищем накопленные сообщения для этого аккаунта и типа события
                logs = session.exec(
                    select(VkBotMessageLog)
                    .where(VkBotMessageLog.account_id == account.id)
                    .where(VkBotMessageLog.event_type == sub.event_type)
                    .where(VkBotMessageLog.status == MessageStatus.PENDING)
                ).all()
                
                if not logs:
                    # Если сообщений нет, просто обновляем время последнего "чека", 
                    # чтобы не проверять каждую минуту, если интервал например 1440 (сутки)
                    sub.last_digest_at = now
                    session.add(sub)
                    continue

                # 3. Формируем дайджест
                header = f"📊 Дайджест уведомлений: {sub.event_type}\n"
                separator = "\n" + "-"*15 + "\n"
                
                # Ограничиваем количество сообщений в одном дайджесте, чтобы не превысить лимиты VK (4096 символов)
                content = []
                current_len = len(header)
                for log in logs:
                    if current_len + len(log.text) + len(separator) > 3800:
                        content.append("... и другие уведомления")
                        break
                    content.append(log.text)
                    current_len += len(log.text) + len(separator)

                combined_text = header + separator + separator.join(content)
                
                # 4. Отправляем в VK
                result = await vk_bot_service.send_message(
                    user_id=account.vk_user_id,
                    message=combined_text,
                    account_id=account.id,
                    event_type=f"digest_{sub.event_type}"
                )
                
                if result["success"]:
                    # Помечаем сообщения как отправленные
                    for log in logs:
                        log.status = MessageStatus.SENT
                        log.sent_at = now
                        session.add(log)
                    
                    sub.last_digest_at = now
                    session.add(sub)
                    logger.info(f"Sent digest for {account.name} (type: {sub.event_type}, count: {len(logs)})")
                else:
                    logger.error(f"Failed to send digest to {account.name}: {result['error']}")
        
        session.commit()
