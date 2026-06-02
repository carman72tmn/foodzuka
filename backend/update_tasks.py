from app.core.database import Session, engine
from app.models.scheduled_task import ScheduledTask
from sqlmodel import select

def update_tasks():
    with Session(engine) as session:
        tasks = session.exec(select(ScheduledTask)).all()
        for t in tasks:
            print(f"Checking task: {t.name} ({t.task_name})")
            if 'app.services.iiko_sync_service.sync_all' in t.task_name:
                print(f"  Updating {t.name}: {t.task_name} -> app.core.scheduler.sync_all")
                t.task_name = 'app.core.scheduler.sync_all'
            if 'app.services.iiko_sync_service.sync_orders_task' in t.task_name:
                print(f"  Updating {t.name}: {t.task_name} -> app.core.scheduler.sync_orders_task")
                t.task_name = 'app.core.scheduler.sync_orders_task'
            session.add(t)
        session.commit()
        print('Tasks updated successfully')

if __name__ == "__main__":
    update_tasks()
