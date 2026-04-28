from app.core.database import SessionLocal
from app.models.sync_log import SyncLog
from sqlalchemy import desc

def check():
    db = SessionLocal()
    try:
        logs = db.query(SyncLog).order_by(desc(SyncLog.created_at)).limit(10).all()
        for log in logs:
            # SyncLog has sync_type, status, details, created_at
            print(f"{log.created_at}: [{log.sync_type}] {log.status} | {log.details[:100] if log.details else 'None'}")
    finally:
        db.close()

if __name__ == "__main__":
    check()
