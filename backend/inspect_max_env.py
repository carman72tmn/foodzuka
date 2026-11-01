from pymax.client_web import WebClient
from sqlmodel import Session, select
from app.core.database import engine
from app.models.chat import MultichatAccount
from app.models.max_settings import MaxSettings, MaxBot

print('WebClient methods:', [m for m in dir(WebClient) if not m.startswith('_')])

with Session(engine) as db:
    s = db.exec(select(MaxSettings)).all()
    print('MaxSettings:', [(x.id, x.is_active, x.base_url, x.api_key) for x in s])
    b = db.exec(select(MaxBot)).all()
    print('MaxBots:', [(x.id, x.bot_name, x.bot_type, x.is_active) for x in b])
    accs = [a for a in db.exec(select(MultichatAccount)).all() if 'max' in (a.channel or '')]
    print('MAX MultichatAccounts:', [(a.id, a.name, a.channel, a.status, a.phone) for a in accs])
