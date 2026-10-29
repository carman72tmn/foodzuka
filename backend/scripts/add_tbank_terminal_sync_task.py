from sqlmodel import Session, select
from app.core.database import engine
from app.models.scheduled_task import ScheduledTask
import json
import uuid

def add_task():
    with Session(engine) as session:
        # Проверяем, есть ли уже такая задача
        existing = session.exec(select(ScheduledTask).where(ScheduledTask.task_name == "app.core.scheduler.sync_tbank_terminals_task_wrapper")).first()
        if existing:
            print("T-Bank terminal sync task already exists")
            return
            
        task = ScheduledTask(
            job_id=str(uuid.uuid4()),
            name="LIVE-мониторинг терминалов Т-Банка",
            task_name="app.core.scheduler.sync_tbank_terminals_task_wrapper",
            trigger_type="interval",
            trigger_value=json.dumps({"minutes": 1}),
            is_active=True,
            description="Опрашивает транзакции POS-терминалов Т-Банка каждую минуту для LIVE-монитора"
        )
        session.add(task)
        session.commit()
        print("T-Bank terminal sync task added successfully")

if __name__ == "__main__":
    add_task()
