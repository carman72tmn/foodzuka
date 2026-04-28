import sys
import os

# Добавляем backend в путь для импорта модулей app
current_dir = os.getcwd()
backend_dir = os.path.join(current_dir, "backend")
if backend_dir not in sys.path:
    sys.path.append(backend_dir)

from sqlmodel import Session, select
from app.core.database import engine
from app.models.customer import Customer
import logging

# Настройка логирования в UTF-8 для корректного отображения кириллицы
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("cleanup_phones")

def cleanup():
    """Очистка номеров телефонов от лишних символов (пробелы, переносы строк)"""
    try:
        with Session(engine) as db:
            customers = db.exec(select(Customer)).all()
            logger.info(f"Найдено {len(customers)} клиентов. Проверка на наличие 'грязных' данных...")
            
            fixed_count = 0
            for customer in customers:
                if not customer.phone:
                    continue
                    
                original_phone = customer.phone
                # Убираем пробелы, переносы строк и спецсимволы
                cleaned_phone = str(original_phone).strip().replace('\r', '').replace('\n', '')
                
                if cleaned_phone != original_phone:
                    logger.info(f"Исправление телефона для клиента {customer.id}: '{original_phone}' -> '{cleaned_phone}'")
                    customer.phone = cleaned_phone
                    fixed_count += 1
                    
            if fixed_count > 0:
                db.commit()
                logger.info(f"Успешно исправлено {fixed_count} номеров телефонов.")
            else:
                logger.info("Грязных данных не обнаружено.")
    except Exception as e:
        logger.error(f"Критическая ошибка при очистке телефонов: {e}", exc_info=True)

if __name__ == "__main__":
    cleanup()
