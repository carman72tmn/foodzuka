from sqlmodel import Session, select
from app.core.database import engine
from app.models.tbank_settings import TBankSettings

db = Session(engine)
s = db.exec(select(TBankSettings)).first()

if s:
    print("Terminal Key:", s.terminal_key)
    print("Token (exists):", bool(s.token))
    print("Certificate (exists):", bool(s.certificate_content))
    print("Selected Terminals:", s.selected_terminals)
    print("Is Active:", s.is_active)
else:
    print("No settings found!")
