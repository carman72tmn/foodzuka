import logging
from sqlmodel import Session, SQLModel, create_engine, text
from app.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Используем тот же DATABASE_URL, что и в приложении
DATABASE_URL = settings.DATABASE_URL
engine = create_engine(DATABASE_URL)

def upgrade():
    logger.info("Starting database migration for VK Contest message templates...")
    
    # Новые столбцы с дефолтными значениями
    new_columns = {
        "msg_miss": ("VARCHAR(500)", "'🎰 {name}, увы! Этот сектор оказался пустым. Попробуйте еще раз!'"),
        "msg_win": ("VARCHAR(500)", "'🎉 Поздравляем, {name}! Вы выиграли приз: {prize}! Инструкция по получению отправлена в ЛС.'"),
        "msg_out_of_attempts": ("VARCHAR(500)", "'❌ {name}, у вас закончились попытки!'"),
        "msg_cooldown": ("VARCHAR(500)", "'⌛ {name}, вы делаете ходы слишком часто! Пожалуйста, подождите еще {cooldown} сек.'"),
        "msg_subscribe_needed": ("VARCHAR(500)", "'⚠️ {name}, вы не подписаны на наше сообщество! Для участия в конкурсе обязательно подпишитесь на группу.'"),
        "msg_like_needed": ("VARCHAR(500)", "'❤️ {name}, для участия необходимо поставить лайк к этому посту!'"),
        "msg_repost_needed": ("VARCHAR(500)", "'📢 {name}, для участия необходимо сделать репост этого поста на свою страницу!'"),
        "msg_invalid_format": ("VARCHAR(500)", "'❓ {name}, я не понял ваш ход. Пожалуйста, напишите правильный формат ходов (например, {example}).'"),
        "msg_pm_congratulations": ("TEXT", "'🎉 Здравствуйте, {name}!\\n\\nВы выиграли в конкурсе «{title}» приз:\\n🎁 {prize}!\\n\\n🔑 Ваш уникальный промокод для заказа: {code}\\n\\nВведите его в корзине при оформлении заказа на сайте или назовите оператору.'")
    }

    with Session(engine) as session:
        # Проверяем существующие колонки в таблице vk_contests
        try:
            # Для PostgreSQL/MySQL получаем список колонок
            res = session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'vk_contests'"))
            existing_columns = [row[0] for row in res.fetchall()]
            logger.info(f"Existing columns in vk_contests: {existing_columns}")
            
            for col_name, (col_type, default_val) in new_columns.items():
                if col_name not in existing_columns:
                    logger.info(f"Adding column '{col_name}' of type {col_type} to vk_contests...")
                    # Выполняем ALTER TABLE
                    session.execute(text(f"ALTER TABLE vk_contests ADD COLUMN {col_name} {col_type} DEFAULT {default_val}"))
                    session.commit()
                    logger.info(f"Column '{col_name}' successfully added.")
                else:
                    logger.info(f"Column '{col_name}' already exists.")
                    
            logger.info("Migration completed successfully!")
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error during migration: {e}")
            raise e

if __name__ == "__main__":
    upgrade()
