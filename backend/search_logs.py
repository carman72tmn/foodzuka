from app.core.database import SessionLocal
from app.models.system_log import SystemLog
from sqlmodel import select

def search_logs(query):
    session = SessionLocal()
    statement = select(SystemLog).where(SystemLog.message.contains(query)).order_by(SystemLog.created_at.desc()).limit(20)
    logs = session.exec(statement).all()
    for l in logs:
        print(f"{l.created_at} [{l.level}] {l.module}: {l.message}")

if __name__ == "__main__":
    search_logs("Resto OLAP v2")
    print("-" * 20)
    search_logs("detailed deliveries")
