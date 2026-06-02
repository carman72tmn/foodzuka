from app.core.database import SessionLocal
from app.models.scheduled_task import ScheduledTask
from sqlmodel import select

def check_tasks():
    session = SessionLocal()
    tasks = session.exec(select(ScheduledTask)).all()
    for t in tasks:
        print(f"Task: {t.name} (ID: {t.job_id})")
        print(f"  Active: {t.is_active}")
        print(f"  Task Name: {t.task_name}")
        print(f"  Last Run: {t.last_run}")
        print("-" * 20)

if __name__ == "__main__":
    check_tasks()
