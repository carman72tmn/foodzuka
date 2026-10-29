"""
Фоновые задачи автоматического создания и ротации бэкапов
"""
import logging
from app.core.database import Session, engine
from app.services.backup_service import backup_service
from app.models.backup_settings import BackupSettings

logger = logging.getLogger(__name__)

def run_automated_backup():
    """Фоновая задача создания авто-бэкапа по расписанию"""
    logger.info("Запуск фоновой задачи резервного копирования...")
    try:
        with Session(engine) as session:
            st = backup_service.get_or_create_settings(session)
            if not st.auto_backup_enabled:
                logger.info("Автоматическое резервное копирование отключено в настройках.")
                return

            backup_type = st.backup_type or "db_and_code"

        # Создание бэкапа и ротация
        res = backup_service.create_backup(backup_type=backup_type)
        logger.info(f"Результат фонового бэкапа: {res}")

    except Exception as e:
        logger.error(f"Ошибка в задаче run_automated_backup: {e}", exc_info=True)


def run_backup_retention():
    """Фоновая задача очистки устаревших архивов"""
    try:
        res = backup_service.apply_retention_policy()
        logger.info(f"Результат ротации бэкапов: {res}")
    except Exception as e:
        logger.error(f"Ошибка в задаче run_backup_retention: {e}")
