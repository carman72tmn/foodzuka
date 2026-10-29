import logging
from sqlmodel import Session
from app.core.database import engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("update_cooking_time")

def run():
    logger.info("Starting cooking time update script...")
    with Session(engine) as session:
        try:
            # Сбрасываем старое дефолтное значение 20 минут в 0 минут для существующих заказов
            result = session.execute("UPDATE orders SET cooking_time_minutes = 0 WHERE cooking_time_minutes = 20;")
            session.commit()
            logger.info(f"Successfully updated cooking_time_minutes from 20 to 0. Rows affected: {result.rowcount}")
        except Exception as e:
            session.rollback()
            logger.error(f"Error executing update query: {e}")

if __name__ == "__main__":
    run()
