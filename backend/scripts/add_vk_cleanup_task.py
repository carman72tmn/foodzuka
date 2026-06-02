from sqlmodel import Session, select
from app.core.database import engine
from app.models.scheduled_task import ScheduledTask
import json
import uuid

def add_task():
    with Session(engine) as session:
        # Проверяем, есть ли уже такая задача
        existing = session.exec(select(ScheduledTask).where(ScheduledTask.task_name == "app.core.scheduler.cleanup_vk_messages_task_wrapper")).first()
        if existing:
            print("Task already exists")
            return
            
        task = ScheduledTask(
            job_id=str(uuid.uuid4()),
            name="Очистка старых сообщений ВК",
            task_name="app.core.scheduler.cleanup_vk_messages_task_wrapper",
            trigger_type="cron",
            trigger_value=json.dumps({"hour": "3", "minute": "0"}), # Каждый день в 3 утра
            is_active=True,
            description="Удаляет сообщения ВК старше 90 дней"
        )
        session.add(task)
        session.commit()
        print("Task added successfully")

if __name__ == "__main__":
    add_task()
