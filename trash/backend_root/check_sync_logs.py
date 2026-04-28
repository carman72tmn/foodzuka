from sqlmodel import Session, select, desc
from app.core.database import engine
from app.models import SyncLog

def check_sync_logs():
    with Session(engine) as session:
        logs = session.exec(select(SyncLog).order_by(desc(SyncLog.id)).limit(10)).all()
        print(f"{'ID':<5} | {'Type':<15} | {'Status':<10} | {'Count':<5} | {'Details'}")
        print("-" * 80)
        for l in logs:
            details = (l.details or "")[:40]
            print(f"{l.id:<5} | {str(l.sync_type):<15} | {str(l.status):<10} | {l.processed_count:<5} | {details}")

if __name__ == "__main__":
    check_sync_logs()
