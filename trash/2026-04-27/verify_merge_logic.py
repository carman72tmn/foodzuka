import sys
import os
from datetime import datetime

# Добавляем путь к backend, чтобы можно было импортировать модули
sys.path.append(os.path.abspath("../backend"))

try:
    from app.services.iiko_sync_service import iiko_sync_service
    from app.models.customer import Customer
    from sqlmodel import Session, create_engine
    
    print("Успешный импорт iiko_sync_service и Customer.")
    
    # Проверяем наличие методов
    methods = [
        "find_customers_missing_iiko_data",
        "merge_customers_by_uid",
        "merge_customers_by_phone",
        "_merge_customer_group"
    ]
    
    for method in methods:
        if hasattr(iiko_sync_service, method):
            print(f"Метод {method} найден в iiko_sync_service.")
        else:
            print(f"ОШИБКА: Метод {method} НЕ НАЙДЕН в iiko_sync_service.")
            
except ImportError as e:
    print(f"Ошибка импорта: {e}")
except Exception as e:
    print(f"Непредвиденная ошибка: {e}")
