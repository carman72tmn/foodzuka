from sqlmodel import Session, select
from app.core.database import engine
from app.models.tbank_settings import TBankSettings

with Session(engine) as session:
    settings = session.exec(select(TBankSettings)).all()
    for s in settings:
        print(f"ID: {s.id}")
        print(f"is_active: {s.is_active}")
        print(f"terminal_key: {s.terminal_key}")
        print(f"selected_terminals: {s.selected_terminals}")
        print(f"terminal_pickup: {s.terminal_pickup}")
        print(f"terminal_delivery: {s.terminal_delivery}")
        print(f"token: {s.token is not None} (len: {len(s.token) if s.token else 0})")
        print(f"certificate_content: {s.certificate_content is not None}")
