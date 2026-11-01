from app.core.database import engine
from sqlmodel import Session, select
from app.models.chat import MultichatMessage
import json

with Session(engine) as s:
    msgs = s.exec(select(MultichatMessage).order_by(MultichatMessage.id.desc())).all()
    found = 0
    for m in msgs:
        p = m.payload or {}
        atts = p.get("attachments") or p.get("attaches") or p.get("attachment")
        if atts and len(atts) > 0:
            found += 1
            print(f"=== Msg ID: {m.id}, Channel: {m.channel}, Peer: {m.peer_id} ===")
            print(f"Attachments in payload: {json.dumps(atts, ensure_ascii=False)[:800]}")
            if found >= 10:
                break
    print(f"\nFound messages with non-empty attachments: {found}")
