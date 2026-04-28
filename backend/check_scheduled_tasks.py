from dotenv import load_dotenv
import os
load_dotenv()

from sqlmodel import Session, select
from app.core.database import engine
from app.models.scheduled_task import ScheduledTask

def check_tasks():
    with Session(engine) as session:
        tasks = session.exec(select(ScheduledTask)).all()
        print(f"Total tasks: {len(tasks)}")
        for task in tasks:
            print(f"- [{task.job_id}] {task.name}: {task.task_name} (Active: {task.is_active}, Trigger: {task.trigger_type})")

if __name__ == "__main__":
    check_tasks()
