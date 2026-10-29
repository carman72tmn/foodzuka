import logging
from sqlmodel import SQLModel
from app.core.database import engine
# Импортируем модели, чтобы они зарегистрировались в метаданных SQLModel
from app.models.vk_contest import VkContest, VkContestPlayer, VkContestWinner

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """Создает таблицы для конкурсов ВК, если их нет"""
    logger.info("Creating VK Contest Bot tables...")
    try:
        # Это создаст только те таблицы, которых еще нет в БД
        SQLModel.metadata.create_all(engine)
        logger.info("VK Contest Bot tables created successfully or already exist.")
    except Exception as e:
        logger.error(f"Failed to create VK Contest Bot tables: {e}", exc_info=True)

if __name__ == "__main__":
    create_tables()
