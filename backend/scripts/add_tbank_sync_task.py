from sqlmodel import Session, select
from app.core.database import engine
from app.models.scheduled_task import ScheduledTask
import json
import uuid

def add_task():
    with Session(engine) as session:
        # Проверяем, есть ли уже такая задача
        existing = session.exec(select(ScheduledTask).where(ScheduledTask.task_name == "app.core.scheduler.sync_tbank_statements_task_wrapper")).first()
        if existing:
            print("T-Bank sync task already exists")
            return
            
        task = ScheduledTask(
            job_id=str(uuid.uuid4()),
            name="Авто-синхронизация выписок Т-Банка",
            task_name="app.core.scheduler.sync_tbank_statements_task_wrapper",
            trigger_type="cron",
            trigger_value=json.dumps({"minute": "0"}), # Запуск каждый час в 00 минут
            is_active=True,
            description="Автоматически загружает выписки Т-Банка за последние 3 дня каждый час"
        )
        session.add(task)
        session.commit()
        print("T-Bank sync task added successfully")

if __name__ == "__main__":
    add_task()
