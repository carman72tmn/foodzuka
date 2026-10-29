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
            # Защита от несовместимых аргументов cron в интервальной задаче
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
                # Проверяем и добавляем задачи для ВКонтакте ботов дней рождения и обложек
                for task_info in [
                    {
                        "name": "Отложенный постинг ВК",
                        "task_name": "app.core.scheduler.vk_scheduler_publish_task_wrapper",
                        "trigger_value": {"minute": "*"},
                        "description": "Проверяет и размещает отложенные посты и сторис во ВКонтакте"
                    },
                    {
                        "name": "Автопубликация поздравлений ВК",
                        "task_name": "app.core.scheduler.vk_birthday_publish_task_wrapper",
                        "trigger_value": {"minute": "*"}, # запускается каждую минуту
                        "description": "Проверяет активных ботов дней рождения и публикует поздравления на стенах групп"
                    },
                    {
                        "name": "Автоудаление поздравлений ВК",
                        "task_name": "app.core.scheduler.vk_birthday_delete_task_wrapper",
                        "trigger_value": {"minute": "*"}, # запускается каждую минуту
                        "description": "Проверяет и удаляет просроченные посты поздравлений именинников со стен"
                    },
                    {
                        "name": "Обновление динамических обложек ВК",
                        "task_name": "app.core.scheduler.vk_cover_update_task_wrapper",
                        "trigger_value": {"minute": "*"}, # запускается каждую минуту
                        "description": "Генерирует и загружает обновленные динамические обложки в ВК группы"
                    },
                    {
                        "name": "Синхронизация активности для обложек ВК",
                        "task_name": "app.core.scheduler.vk_cover_activity_sync_task_wrapper",
                        "trigger_value": {"minute": "*/30"}, # запускается каждые 30 минут
                        "description": "Считает лайки и комментарии в группах ВК для вывода топ-активных подписчиков"
                    },
                    {
                        "name": "Отправка напоминаний о попытках ВК",
                        "task_name": "app.core.scheduler.vk_contest_reminders_task_wrapper",
                        "trigger_type": "cron",
                        "trigger_value": {"minute": "*/10"}, # запускается каждые 10 минут
                        "description": "Проверяет игроков с неиспользованными попытками в активных конкурсах и присылает им комментарии-напоминания"
                    },
                    {
                        "name": "Мультичат: Синхронизация личного ВК",
                        "task_name": "app.core.scheduler.multichat_sync_vk_user_task_wrapper",
                        "trigger_type": "interval",
                        "trigger_value": {"minutes": 15}, # каждые 15 минут (с защитой от Flood Control)
                        "description": "Синхронизирует сообщения и диалоги из подключенных личных аккаунтов ВКонтакте"
                    },
                    {
                        "name": "Мультичат: Синхронизация личного MAX",
                        "task_name": "app.core.scheduler.multichat_sync_max_user_task_wrapper",
                        "trigger_type": "interval",
                        "trigger_value": {"minutes": 5}, # каждые 5 минут
                        "description": "Синхронизирует сообщения и диалоги из подключенных личных аккаунтов MAX (Web Instance Bridge)"
                    }
                ]:
                    existing = session.exec(
                        select(ScheduledTask).where(ScheduledTask.task_name == task_info["task_name"])
                    ).first()
                    if not existing:
                        import uuid
                        import json
                        t_type = task_info.get("trigger_type", "cron")
                        task = ScheduledTask(
                            job_id=str(uuid.uuid4()),
                            name=task_info["name"],
                            task_name=task_info["task_name"],
                            trigger_type=t_type,
                            trigger_value=json.dumps(task_info["trigger_value"]),
                            is_active=True,
                            description=task_info["description"]
                        )
                        session.add(task)
                session.commit()

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
    """Полная синхронизация всего из iiko (Меню + Категории + Стоп-листы + Ночная сверка заказов)"""
    from app.services.iiko_sync_service import iiko_sync_service
    from app.core.database import Session, engine
    with Session(engine) as session:
        logger.info("Запуск полной синхронизации (Меню + Категории + Стоп-листы)")
        await iiko_sync_service.sync_categories_only(session)
        await iiko_sync_service.sync_menu(session)
        await iiko_sync_service.sync_stop_lists(session)
        # Ночью в 03:00 один раз делаем полную глубокую сверку заказов за 24 часа
        await iiko_sync_service.sync_orders(session, hours=24, fast_only=False)
        logger.info("Полная ночная синхронизация завершена")

async def sync_orders_task(hours: int = 2, fast_only: bool = True):
    """Синхронизация заказов (быстрый инкрементальный режим через ревизии без перегрузки iiko)"""
    from app.services.iiko_sync_service import iiko_sync_service
    from app.core.database import Session, engine
    with Session(engine) as session:
        logger.info(f"Запуск быстрой плановой синхронизации заказов (fast_only={fast_only}, hours={hours})")
        await iiko_sync_service.sync_orders(session, hours=hours, fast_only=fast_only)

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
    from app.models.sync_log import SyncStatus
    from app.core.database import Session, engine
    with Session(engine) as session:
        status = SyncStatus(
            task_id=f"nightly_{int(datetime.now().timestamp())}",
            sync_type="customers",
            status="pending",
            total_count=0,
            processed_count=0,
            added_count=0,
            updated_count=0,
            details="Инициализация ночной синхронизации клиентов"
        )
        session.add(status)
        session.commit()
        session.refresh(status)
        task = sync_customers_batch.delay(0, status.id, False)
        status.task_id = task.id
        status.status = "running"
        session.add(status)
        session.commit()

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


async def sync_courier_task(days: int = 1):
    """Синхронизация доставок курьеров (оперативный опрос за текущий день)"""
    from app.tasks.general_tasks import sync_courier_deliveries_task
    sync_courier_deliveries_task.delay(days=days)

async def cleanup_logs_task():
    """Очистка старых логов"""
    from app.services.system_service import cleanup_old_logs
    await cleanup_old_logs()

async def cleanup_vk_messages_task_wrapper():
    """Очистка старых сообщений ВК (старше 90 дней)"""
    from app.tasks.vk_parser_tasks import cleanup_vk_messages_task
    # Вызываем через delay для выполнения в воркере
    cleanup_vk_messages_task.delay()

async def sync_tbank_statements_task_wrapper():
    """Автоматическая синхронизация выписок Т-Банка (Celery-враппер)"""
    from app.tasks.tbank_tasks import sync_tbank_statements_task
    sync_tbank_statements_task.delay()


async def sync_tbank_terminals_task_wrapper():
    """Автоматический опрос POS-терминалов Т-Банка (Celery-враппер)"""
    from app.tasks.tbank_tasks import sync_tbank_terminals_task
    sync_tbank_terminals_task.delay()


async def vk_birthday_publish_task_wrapper():
    """Автоматическая публикация поздравлений ВК (Celery-враппер)"""
    from app.tasks.vk_birthday_task import vk_birthday_publish_task
    vk_birthday_publish_task.delay()


async def vk_birthday_delete_task_wrapper():
    """Автоматическое удаление постов поздравлений ВК (Celery-враппер)"""
    from app.tasks.vk_birthday_task import vk_birthday_delete_task
    vk_birthday_delete_task.delay()


async def vk_cover_update_task_wrapper():
    """Периодическое обновление обложек ВК (Celery-враппер)"""
    from app.tasks.vk_cover_task import vk_cover_update_task
    vk_cover_update_task.delay()


async def vk_cover_activity_sync_task_wrapper():
    """Синхронизация активности пользователей ВК для обложек (Celery-враппер)"""
    from app.tasks.vk_cover_task import vk_cover_activity_sync_task
    vk_cover_activity_sync_task.delay()


async def vk_contest_reminders_task_wrapper():
    """Периодическая отправка напоминаний о попытках ВК (Celery-враппер)"""
    from app.tasks.vk_contest_reminders_task import vk_contest_reminders_task
    vk_contest_reminders_task.delay()


async def vk_scheduler_publish_task_wrapper():
    """Периодическая проверка и отправка отложенных публикаций ВК (Celery-враппер)"""
    from app.tasks.vk_scheduler_task import run_vk_post_scheduler
    run_vk_post_scheduler.delay()


async def cleanup_chat_media_task_wrapper():
    """Очистка кэша изображений мультичата (старше 48 дней)"""
    from app.services.chat_media_cache_service import chat_media_cache_service
    chat_media_cache_service.cleanup_expired_cache(days=48)


async def multichat_sync_vk_user_task_wrapper():
    """Фоновая синхронизация личных аккаунтов ВКонтакте для Мультичата (в фоновом потоке)"""
    def _sync():
        try:
            from app.services.multichat_user_service import multichat_user_service
            from app.core.database import Session, engine
            with Session(engine) as session:
                multichat_user_service.sync_vk_user_dialogs(session)
        except Exception as e:
            logger.error(f"Ошибка фоновой синхронизации VK в Мультичате: {e}")
            
    await asyncio.to_thread(_sync)


async def multichat_sync_max_user_task_wrapper():
    """Фоновая синхронизация личных аккаунтов MAX (Web Instance Bridge) для Мультичата"""
    try:
        from app.services.max_bridge_service import max_bridge_service
        await max_bridge_service.sync_pymax_dialogs()
    except Exception as e:
        logger.error(f"Ошибка фоновой синхронизации MAX в Мультичате: {e}")
