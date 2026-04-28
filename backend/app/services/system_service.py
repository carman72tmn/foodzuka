import logging
from datetime import datetime, timedelta
from sqlmodel import Session, select, delete
from app.core.database import engine
from app.models.sync_log import SyncLog

logger = logging.getLogger(__name__)

async def cleanup_old_logs(days: int = 30):
    """Удаление логов синхронизации старше N дней"""
    try:
        limit = datetime.now() - timedelta(days=days)
        with Session(engine) as session:
            # Используем SQL-запрос для массового удаления
            from sqlalchemy import text
            session.execute(text(f"DELETE FROM sync_logs WHERE created_at < '{limit.isoformat()}'"))
            session.commit()
            logger.info(f"Очистка логов завершена (старше {days} дней)")
    except Exception as e:
        logger.error(f"Ошибка при очистке логов: {e}")
