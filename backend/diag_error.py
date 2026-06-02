from app.core.database import SessionLocal
from app.models.system_log import SystemLog
from sqlmodel import select
import os

def get_last_error():
    session = SessionLocal()
    # Search for the specific error message
    statement = select(SystemLog).where(SystemLog.message.contains("IikoSettings")).order_by(SystemLog.created_at.desc()).limit(1)
    log = session.exec(statement).first()
    if log:
        print(f"--- MESSAGE ---\n{log.message}\n")
        print(f"--- STACK TRACE ---\n{log.stack_trace}")
    else:
        print("No matching logs found.")

if __name__ == "__main__":
    get_last_error()
