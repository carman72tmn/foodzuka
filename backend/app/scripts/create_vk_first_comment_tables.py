import sys
import os
import logging

# Добавляем путь к backend, чтобы можно было импортировать модули приложения
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sqlmodel import SQLModel
from app.core.database import engine
# Импортируем модели, чтобы они зарегистрировались в метаданных SQLModel
from app.models.vk_first_comment_settings import VkFirstCommentSettings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Создает таблицы для бота первокомментов ВК, если их нет"""
    logger.info("Creating VK First Comment Bot tables...")
    try:
        # Это создаст только те таблицы, которых еще нет в БД
        SQLModel.metadata.create_all(engine)
        logger.info("VK First Comment Bot tables created successfully or already exist.")
    except Exception as e:
        logger.error(f"Failed to create VK First Comment Bot tables: {e}", exc_info=True)

if __name__ == "__main__":
    create_tables()
