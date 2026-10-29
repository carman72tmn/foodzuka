"""
Задачи Celery для парсера VK
"""
import asyncio
import logging
from sqlmodel import Session, select
from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.vk_settings import VkSettings
from app.models.vk_bot_connection import VkBotConnection
from app.services.vk_service import scan_historical_messages
from app.core.datetime_utils import utc_now

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.vk_parser_tasks.scan_vk_history_task")
def scan_vk_history_task(self, bot_id: int | None = None):
    """
    Задача для ретроспективного сканирования истории сообщений VK
    """
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    with Session(engine) as db:
        bot = None
        if bot_id:
            bot = db.get(VkBotConnection, bot_id)
            if not bot:
                logger.error(f"VK Bot {bot_id} not found, skipping scan")
                return f"Error: Bot {bot_id} not found"
            bot_token = bot.vk_bot_token
            group_id = bot.vk_group_id
        else:
            vk_settings = db.exec(select(VkSettings)).first()
            if not vk_settings or not vk_settings.vk_bot_token:
                logger.error("VK Bot Token not configured, skipping scan")
                return "Error: Token not configured"
            bot_token = vk_settings.vk_bot_token
            group_id = vk_settings.vk_group_id

        started_at = utc_now().isoformat()
        
        # Инициализируем статус
        initial_status = {
            "status": "running",
            "progress": 0,
            "total": 0,
            "matches": 0,
            "started_at": started_at
        }
        
        if bot_id and bot:
            bot.scan_status = initial_status
            db.add(bot)
        else:
            vk_settings = db.exec(select(VkSettings)).first()
            if vk_settings:
                vk_settings.vk_parser_scan_status = initial_status
                db.add(vk_settings)
        db.commit()

        # Callback для обновления прогресса
        async def on_progress(processed, total, matches):
            with Session(engine) as progress_db:
                status_dict = {
                    "status": "running",
                    "progress": processed,
                    "total": total,
                    "matches": matches,
                    "started_at": started_at
                }
                if bot_id:
                    progress_bot = progress_db.get(VkBotConnection, bot_id)
                    if progress_bot:
                        progress_bot.scan_status = status_dict
                        progress_db.add(progress_bot)
                else:
                    settings = progress_db.exec(select(VkSettings)).first()
                    if settings:
                        settings.vk_parser_scan_status = status_dict
                        progress_db.add(settings)
                progress_db.commit()

        # 2. Запускаем сканирование
        try:
            result = loop.run_until_complete(
                scan_historical_messages(db, bot_token, group_id, on_progress=on_progress)
            )
            
            # 3. Финализируем
            with Session(engine) as db_final:
                if bot_id:
                    final_bot = db_final.get(VkBotConnection, bot_id)
                    if final_bot:
                        if "error" in result:
                            final_bot.scan_status = {
                                "status": "error",
                                "error": result["error"],
                                "started_at": started_at
                            }
                        else:
                            completed_at = result["completed_at"]
                            final_bot.scan_status = {
                                "status": "completed",
                                "progress": result["conversations_processed"],
                                "total": result["conversations_processed"],
                                "matches": result["matches_found"],
                                "started_at": started_at,
                                "completed_at": completed_at.isoformat()
                            }
                            final_bot.last_scan_at = completed_at
                        db_final.add(final_bot)
                else:
                    final_settings = db_final.exec(select(VkSettings)).first()
                    if final_settings:
                        if "error" in result:
                            final_settings.vk_parser_scan_status = {
                                "status": "error",
                                "error": result["error"],
                                "started_at": started_at
                            }
                        else:
                            completed_at = result["completed_at"]
                            final_settings.vk_parser_scan_status = {
                                "status": "completed",
                                "progress": result["conversations_processed"],
                                "total": result["conversations_processed"],
                                "matches": result["matches_found"],
                                "started_at": started_at,
                                "completed_at": completed_at.isoformat()
                            }
                            final_settings.vk_parser_last_scan_at = completed_at
                        db_final.add(final_settings)
                db_final.commit()
            
            return f"Scan completed: {result.get('matches_found', 0)} matches"
            
        except Exception as e:
            logger.error(f"Failed to scan VK history: {e}")
            with Session(engine) as db_error:
                if bot_id:
                    err_bot = db_error.get(VkBotConnection, bot_id)
                    if err_bot:
                        err_bot.scan_status = {
                            "status": "error",
                            "error": str(e),
                            "started_at": started_at
                        }
                        db_error.add(err_bot)
                else:
                    err_settings = db_error.exec(select(VkSettings)).first()
                    if err_settings:
                        err_settings.vk_parser_scan_status = {
                            "status": "error",
                            "error": str(e),
                            "started_at": started_at
                        }
                        db_error.add(err_settings)
                db_error.commit()
            raise e

@celery_app.task(name="app.tasks.vk_parser_tasks.cleanup_vk_messages_task")
def cleanup_vk_messages_task():
    """
    Задача для удаления сообщений ВК старше 90 дней и истории активностей старше 12 месяцев
    """
    from app.models.vk_message import VkMessage
    from app.models.vk_activity import VkActivity
    from datetime import timedelta
    from sqlalchemy import delete
    
    threshold = utc_now() - timedelta(days=90)
    activity_threshold = utc_now() - timedelta(days=365)
    
    with Session(engine) as db:
        try:
            # 1. Удаление старых сообщений
            statement = delete(VkMessage).where(VkMessage.created_at < threshold)
            result = db.exec(statement)
            deleted_count = result.rowcount
            
            # 2. Удаление старых активностей (12 месяцев)
            activity_statement = delete(VkActivity).where(VkActivity.created_at < activity_threshold)
            activity_result = db.exec(activity_statement)
            deleted_activities = activity_result.rowcount
            
            db.commit()
            
            logger.info(f"Cleanup task: deleted {deleted_count} messages older than {threshold} and {deleted_activities} activities older than {activity_threshold}")
            return f"Deleted {deleted_count} messages and {deleted_activities} activities"
        except Exception as e:
            logger.error(f"Failed to cleanup VK data: {e}")
            db.rollback()
            return f"Error: {str(e)}"
