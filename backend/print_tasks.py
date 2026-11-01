from sqlmodel import Session, select
from app.core.database import engine
from sqlalchemy import text

db = Session(engine)
res = db.execute(text("SELECT id, name, task_name, trigger_value, is_active FROM scheduled_tasks;")).all()

print(f"Scheduled tasks found: {len(res)}")
for r in res:
    print(r)
