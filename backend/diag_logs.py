from app.core.database import SessionLocal
from app.models.system_log import SystemLog
from sqlmodel import select
import os

def list_recent_logs(limit=20):
    session = SessionLocal()
    statement = select(SystemLog).order_by(SystemLog.created_at.desc()).limit(limit)
    logs = session.exec(statement).all()
    for l in logs:
        print(f"{l.created_at} [{l.level}] {l.module}: {l.message}")
        if l.level in ["ERROR", "CRITICAL"] and l.stack_trace:
             print(f"--- STACK TRACE ---\n{l.stack_trace}\n")

if __name__ == "__main__":
    list_recent_logs()
