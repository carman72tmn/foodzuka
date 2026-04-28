"""
Конфигурация Celery для FoodTech
"""
from celery import Celery
from app.core.config import settings

# Инициализация Celery
celery_app = Celery(
    "foodtech",
    broker=settings.REDIS_URL or "redis://localhost:6379/0",
    backend=settings.REDIS_URL or "redis://localhost:6379/0",
    include=["app.tasks.customer_tasks", "app.tasks.general_tasks"]
)

# Настройки Celery
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Yekaterinburg",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
)

from celery.signals import task_failure, task_postrun
from app.models.system_log import SystemLog
from app.core.database import SessionLocal

@task_failure.connect
def handle_task_failure(sender=None, exception=None, task_id=None, traceback=None, **kwargs):
    """Логирование ошибок задач Celery в системный лог"""
    import traceback as tb
    stack_trace_str = "".join(tb.format_exception(type(exception), exception, traceback))
    with SessionLocal() as session:
        log = SystemLog(
            level="ERROR",
            module=f"Celery:{sender.name if sender else 'unknown'}",
            message=f"Ошибка в задаче {task_id}: {str(exception)}",
            stack_trace=stack_trace_str
        )
        session.add(log)
        session.commit()

@task_postrun.connect
def handle_task_postrun(sender=None, task_id=None, state=None, **kwargs):
    """Логирование завершения задач Celery (успех/ошибка)"""
    if state == 'SUCCESS':
        with SessionLocal() as session:
            log = SystemLog(
                level="INFO",
                module=f"Celery:{sender.name if sender else 'unknown'}",
                message=f"Задача завершена успешно: {task_id}"
            )
            session.add(log)
            session.commit()

if __name__ == "__main__":
    celery_app.start()
