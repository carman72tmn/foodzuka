from sqlmodel import Session, select
from app.core.database import engine
from app.models.sync_log import SyncLog

with Session(engine) as session:
    logs = session.exec(select(SyncLog).order_by(SyncLog.id.desc()).limit(10)).all()
    for l in logs:
        print(f"ID: {l.id} | Type: {l.sync_type} | Status: {l.status} | Details: {l.details}")
