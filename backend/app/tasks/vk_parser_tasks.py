"""
Задачи Celery для парсера VK
"""
import asyncio
import logging
from sqlmodel import Session, select
from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.vk_settings import VkSettings
from app.services.vk_service import scan_historical_messages
from app.core.datetime_utils import utc_now

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.vk_parser_tasks.scan_vk_history_task")
def scan_vk_history_task(self):
    """
    Задача для ретроспективного сканирования истории сообщений VK
    """
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    with Session(engine) as db:
        # 1. Получаем настройки
        vk_settings = db.exec(select(VkSettings)).first()
        if not vk_settings or not vk_settings.vk_bot_token:
            logger.error("VK Bot Token not configured, skipping scan")
            return "Error: Token not configured"

        bot_token = vk_settings.vk_bot_token
        group_id = vk_settings.vk_group_id

        # Инициализируем статус
        vk_settings.vk_parser_scan_status = {
            "status": "running",
            "progress": 0,
            "total": 0,
            "matches": 0,
            "started_at": utc_now().isoformat()
        }
        db.add(vk_settings)
        db.commit()

        # Callback для обновления прогресса
        async def on_progress(processed, total, matches):
            # Используем отдельную сессию для промежуточных обновлений, 
            # чтобы не блокировать основную транзакцию (хотя в sqlite это может быть проблемой)
            # В postgres это ок.
            with Session(engine) as progress_db:
                settings = progress_db.exec(select(VkSettings)).first()
                if settings:
                    settings.vk_parser_scan_status = {
                        "status": "running",
                        "progress": processed,
                        "total": total,
                        "matches": matches,
                        "started_at": vk_settings.vk_parser_scan_status["started_at"]
                    }
                    progress_db.add(settings)
                    progress_db.commit()

        # 2. Запускаем сканирование
        try:
            result = loop.run_until_complete(
                scan_historical_messages(db, bot_token, group_id, on_progress=on_progress)
            )
            
            # 3. Финализируем
            with Session(engine) as db_final:
                final_settings = db_final.exec(select(VkSettings)).first()
                if final_settings:
                    if "error" in result:
                        final_settings.vk_parser_scan_status["status"] = "error"
                        final_settings.vk_parser_scan_status["error"] = result["error"]
                    else:
                        final_settings.vk_parser_scan_status = {
                            "status": "completed",
                            "progress": result["conversations_processed"],
                            "total": result["conversations_processed"],
                            "matches": result["matches_found"],
                            "started_at": vk_settings.vk_parser_scan_status["started_at"],
                            "completed_at": result["completed_at"].isoformat()
                        }
                        final_settings.vk_parser_last_scan_at = result["completed_at"]
                    
                    db_final.add(final_settings)
                    db_final.commit()
            
            return f"Scan completed: {result.get('matches_found', 0)} matches"
            
        except Exception as e:
            logger.error(f"Failed to scan VK history: {e}")
            with Session(engine) as db_error:
                err_settings = db_error.exec(select(VkSettings)).first()
                if err_settings:
                    err_settings.vk_parser_scan_status["status"] = "error"
                    err_settings.vk_parser_scan_status["error"] = str(e)
                    db_error.add(err_settings)
                    db_error.commit()
            raise e

@celery_app.task(name="app.tasks.vk_parser_tasks.cleanup_vk_messages_task")
def cleanup_vk_messages_task():
    """
    Задача для удаления сообщений ВК старше 90 дней
    """
    from app.models.vk_message import VkMessage
    from datetime import timedelta
    from sqlalchemy import delete
    
    threshold = utc_now() - timedelta(days=90)
    
    with Session(engine) as db:
        try:
            statement = delete(VkMessage).where(VkMessage.created_at < threshold)
            result = db.exec(statement)
            db.commit()
            
            deleted_count = result.rowcount
            logger.info(f"Cleanup task: deleted {deleted_count} messages older than {threshold}")
            return f"Deleted {deleted_count} messages"
        except Exception as e:
            logger.error(f"Failed to cleanup VK messages: {e}")
            db.rollback()
            return f"Error: {str(e)}"
