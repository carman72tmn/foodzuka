"""
Миграция для создания таблицы запланированных задач и инициализации базовых заданий
"""
import sys
import os
from datetime import datetime, timezone

# Добавляем путь к backend в PYTHONPATH
sys.path.append(os.path.join(os.getcwd(), 'backend'))

from sqlmodel import SQLModel, Session, select
from app.core.database import engine
from app.models.scheduled_task import ScheduledTask

def migrate():
    # 1. Создаем таблицы (если не существуют)
    print("Создание таблиц...")
    SQLModel.metadata.create_all(engine)
    
    with Session(engine) as session:
        # 2. Проверяем наличие базовых задач
        tasks_to_add = [
            {
                "job_id": "sync_all",
                "name": "Полная синхронизация iiko (Меню + Гости)",
                "task_name": "app.services.iiko_sync_service.sync_all",
                "trigger_type": "cron",
                "trigger_value": '{"hour": 3, "minute": 0}',
                "description": "Ежедневная полная выгрузка меню и базы клиентов в 3:00"
            },
            {
                "job_id": "sync_orders_hourly",
                "name": "Синхронизация заказов (каждый час)",
                "task_name": "app.services.iiko_sync_service.sync_orders_task",
                "trigger_type": "interval",
                "trigger_value": '{"hours": 1}',
                "args": '[24]',  # 24 часа глубина
                "description": "Синхронизация заказов за последние 24 часа"
            },
            {
                "job_id": "sync_today_revenue",
                "name": "Синхронизация выручки (сегодня)",
                "task_name": "app.services.revenue_sync.sync_today_revenue",
                "trigger_type": "interval",
                "trigger_value": '{"minutes": 30}',
                "description": "Синхронизация выручки за текущий день каждые 30 минут"
            },
            {
                "job_id": "sync_yesterday_revenue",
                "name": "Синхронизация выручки (вчера)",
                "task_name": "app.services.revenue_sync.sync_yesterday_revenue",
                "trigger_type": "cron",
                "trigger_value": '{"hour": 0, "minute": 5}',
                "description": "Финальная синхронизация выручки за вчерашний день в 00:05"
            },
            {
                "job_id": "cleanup_logs",
                "name": "Очистка старых логов",
                "task_name": "app.services.system_service.cleanup_old_logs",
                "trigger_type": "cron",
                "trigger_value": '{"day_of_week": "mon", "hour": 4, "minute": 0}',
                "description": "Очистка логов синхронизации старше 30 дней (по понедельникам)"
            },
            {
                "name": "Синхронизация смен",
                "task_name": "app.core.scheduler.sync_shifts_task",
                "job_id": "sync_shifts",
                "trigger_type": "interval",
                "trigger_value": '{"minutes": 10}',
                "description": "Синхронизация смен сотрудников из iiko каждые 10 минут"
            },
            {
                "name": "Синхронизация заказов",
                "task_name": "app.core.scheduler.sync_orders_task",
                "job_id": "sync_orders",
                "trigger_type": "interval",
                "trigger_value": '{"minutes": 10}',
                "description": "Синхронизация статусов заказов из iiko каждые 10 минут"
            },
            {
                "name": "Дайджест VK",
                "task_name": "app.tasks.vk_digest_task.process_vk_digests",
                "job_id": "vk_digest",
                "trigger_type": "interval",
                "trigger_value": '{"minutes": 1}',
                "description": "Рассылка дайджестов в VK каждую минуту"
            },
            {
                "name": "Ежедневная очистка базы",
                "task_name": "app.tasks.customer_tasks.sync_customers_batch",
                "job_id": "nightly_sync",
                "trigger_type": "cron",
                "trigger_value": '{"hour": 3, "minute": 0}',
                "args": '[0, 0, true]', # skip=0, status_id=0 (placeholder), force_update=True
                "description": "Полная синхронизация клиентов в 03:00 ночи"
            }

        ]
        
        for task_data in tasks_to_add:
            existing = session.exec(
                select(ScheduledTask).where(ScheduledTask.job_id == task_data["job_id"])
            ).first()
            
            if not existing:
                print(f"Добавление задачи: {task_data['name']}")
                new_task = ScheduledTask(**task_data)
                session.add(new_task)
            else:
                print(f"Задача {task_data['name']} уже существует")
                
        session.commit()
    print("Миграция завершена успешно.")

if __name__ == "__main__":
    migrate()
