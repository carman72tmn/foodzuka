import logging
import asyncio
from datetime import datetime, timezone, timedelta
from typing import List, Dict, Any, Optional
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.executors.asyncio import AsyncIOExecutor
from apscheduler.executors.pool import ThreadPoolExecutor, ProcessPoolExecutor
from apscheduler.events import EVENT_JOB_EXECUTED, EVENT_JOB_ERROR
from sqlmodel import Session, select
from app.core.database import engine
from app.models.scheduled_task import ScheduledTask
from app.models.sync_log import SyncLog

logger = logging.getLogger(__name__)

# Конфигурация хранилища задач в БД
jobstores = {
    'default': SQLAlchemyJobStore(engine=engine)
}

# Настройка исполнителей: AsyncIOExecutor для асинхронных задач, 
# ThreadPoolExecutor для потенциально блокирующих синхронных задач
executors = {
    'default': AsyncIOExecutor(),
    'threadpool': ThreadPoolExecutor(20)
}

job_defaults = {
    'coalesce': False,
    'max_instances': 3,
    'misfire_grace_time': 300  # Увеличено до 5 минут для надежности
}

# Инициализация планировщика
scheduler = AsyncIOScheduler(
    jobstores=jobstores, 
    executors=executors, 
    job_defaults=job_defaults,
    timezone='UTC' # Временное переключение на UTC для стабильности
)

def job_listener(event):
    """Слушатель событий планировщика для обновления статуса задач в нашей таблице"""
    with Session(engine) as session:
        task = session.exec(select(ScheduledTask).where(ScheduledTask.job_id == event.job_id)).first()
        if not task:
            return

        now = datetime.now()
        task.last_run = now
        
        if event.exception:
            logger.error(f"Задача {event.job_id} завершилась с ошибкой: {event.exception}")
        else:
            logger.info(f"Задача {event.job_id} успешно выполнена")
            
            # Проверка зависимостей (цепочки задач)
            dependents = session.exec(
                select(ScheduledTask).where(
                    ScheduledTask.trigger_after_job_id == event.job_id,
                    ScheduledTask.is_active == True
                )
            ).all()
            
            for dep in dependents:
                logger.info(f"Запуск зависимой задачи: {dep.name} (после {task.name})")
                try:
                    # Запускаем зависимую задачу как разовую
                    import importlib
                    module_path, func_name = dep.task_name.rsplit('.', 1)
                    module = importlib.import_module(module_path)
                    func = getattr(module, func_name)
                    
                    # AsyncIOScheduler умеет работать с async функциями
                    scheduler.add_job(func, args=dep.get_args(), kwargs=dep.get_kwargs())
                except Exception as e:
                    logger.error(f"Ошибка при запуске зависимой задачи {dep.name}: {e}")

        session.add(task)
        session.commit()

scheduler.add_listener(job_listener, EVENT_JOB_EXECUTED | EVENT_JOB_ERROR)

def add_scheduled_job(task: ScheduledTask):
    """Добавление задачи в APScheduler на основе модели ScheduledTask"""
    try:
        import importlib
        module_path, func_name = task.task_name.rsplit('.', 1)
        module = importlib.import_module(module_path)
        func = getattr(module, func_name)
        
        trigger_params = task.get_trigger_params()
        
        if task.trigger_type == "interval":
            scheduler.add_job(
                func, 
                "interval", 
                id=task.job_id,
                args=task.get_args(),
                kwargs=task.get_kwargs(),
                replace_existing=True,
                misfire_grace_time=60,
                **trigger_params
            )
        elif task.trigger_type == "cron":
            if isinstance(trigger_params, dict) and "expression" in trigger_params:
                from apscheduler.triggers.cron import CronTrigger
                trigger = CronTrigger.from_crontab(trigger_params["expression"])
                scheduler.add_job(
                    func, 
                    trigger, 
                    id=task.job_id,
                    args=task.get_args(),
                    kwargs=task.get_kwargs(),
                    replace_existing=True,
                    misfire_grace_time=60
                )
            else:
                scheduler.add_job(
                    func, 
                    "cron", 
                    id=task.job_id,
                    args=task.get_args(),
                    kwargs=task.get_kwargs(),
                    replace_existing=True,
                    misfire_grace_time=60,
                    **trigger_params
                )
        return True
    except Exception as e:
        logger.error(f"Ошибка при добавлении задачи {task.name} в планировщик: {e}")
        return False

def start_scheduler():
    """Инициализация и запуск планировщика"""
    print("DEBUG: Calling start_scheduler()")
    if not scheduler.running:
        try:
            # Запускаем планировщик
            scheduler.start()
            print("DEBUG: AsyncIOScheduler started")
            logger.info("AsyncIOScheduler запущен")
            
            # Загружаем активные задачи из нашей таблицы
            with Session(engine) as session:
                tasks = session.exec(select(ScheduledTask).where(ScheduledTask.is_active == True)).all()
                print(f"DEBUG: Found {len(tasks)} active tasks in DB")
                for task in tasks:
                    if task.trigger_type != "dependency":
                        success = add_scheduled_job(task)
                        print(f"DEBUG: Adding job {task.name}: {'success' if success else 'FAILED'}")
                
                logger.info(f"Загружено {len(tasks)} активных задач из базы данных")
        except Exception as e:
            print(f"ERROR in start_scheduler: {e}")
            logger.error(f"Ошибка при запуске планировщика: {e}")
    else:
        print("DEBUG: Scheduler is already running")

async def get_scheduler_info():
    """Получение информации о текущих задачах в планировщике"""
    jobs = scheduler.get_jobs()
    return [{
        "id": job.id,
        "name": job.name,
        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        "trigger": str(job.trigger)
    } for job in jobs]

# --- Wrappers for tasks ---

async def sync_all():
    """Полная синхронизация всего из iiko (Меню + Категории + Стоп-листы)"""
    from app.services.iiko_sync_service import iiko_sync_service
    from app.core.database import Session, engine
    with Session(engine) as session:
        logger.info("Запуск полной синхронизации (Меню + Категории + Стоп-листы)")
        await iiko_sync_service.sync_categories_only(session)
        await iiko_sync_service.sync_menu(session)
        await iiko_sync_service.sync_stop_lists(session)
        logger.info("Полная синхронизация завершена")

async def sync_orders_task(hours: int = 24):
    """Синхронизация заказов (обертка) за указанный период"""
    from app.services.iiko_sync_service import iiko_sync_service
    from app.core.database import Session, engine
    with Session(engine) as session:
        logger.info(f"Запуск плановой синхронизации заказов за {hours} ч.")
        await iiko_sync_service.sync_orders(session, hours=hours)

async def sync_shifts_task():
    """Синхронизация сотрудников и смен (обертка)"""
    from app.services.iiko_sync_service import iiko_sync_service
    from app.core.database import Session, engine
    with Session(engine) as session:
        # Используем sync_employees_full который включает смены
        await iiko_sync_service.sync_employees_full(session)

async def sync_customers_task():
    """Ночная синхронизация гостей (обертка)"""
    from app.tasks.customer_tasks import sync_customers_batch
    # Это Celery задача, но мы можем вызвать её синхронно/асинхронно через Celery или напрямую
    # Для простоты вызываем сервис напрямую если возможно, или через delay
    sync_customers_batch.delay()

async def vk_digest_task():
    """Рассылка дайджестов VK (обертка)"""
    from app.tasks.vk_digest_task import process_vk_digests
    await process_vk_digests()

async def sync_revenue_task():
    """Синхронизация выручки и OLAP данных (обертка)"""
    from app.services.revenue_sync import revenue_sync_service
    await revenue_sync_service.sync_today_revenue()

async def sync_yesterday_revenue_task():
    """Синхронизация выручки за вчерашний день (обертка)"""
    from app.services.revenue_sync import revenue_sync_service
    await revenue_sync_service.sync_yesterday_revenue()


async def sync_courier_task():
    """Синхронизация доставок курьеров (обертка)"""
    from app.services.iiko_sync_service import iiko_sync_service
    from app.core.database import Session, engine
    with Session(engine) as session:
        await iiko_sync_service.sync_courier_deliveries(session)

async def cleanup_logs_task():
    """Очистка старых логов"""
    from app.services.system_service import cleanup_old_logs
    await cleanup_old_logs()

async def cleanup_vk_messages_task_wrapper():
    """Очистка старых сообщений ВК (старше 90 дней)"""
    from app.tasks.vk_parser_tasks import cleanup_vk_messages_task
    # Вызываем через delay для выполнения в воркере
    cleanup_vk_messages_task.delay()
