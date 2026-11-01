import json
from sqlmodel import Session
from app.core.database import engine
from app.models.chat import MultichatAccount

with Session(engine) as db:
    acc = db.get(MultichatAccount, 10)
    if acc:
        print('ID:', acc.id)
        print('Name:', acc.name)
        print('Channel:', acc.channel)
        print('Status:', acc.status)
        print('Phone:', acc.phone)
        print('Token:', acc.token)
        print('Session string:', acc.session_string)
