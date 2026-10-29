from sqlmodel import Session, text
from app.core.database import engine

with Session(engine) as session:
    res = session.execute(text('select * from tbank_settings')).mappings().all()
    for row in res:
        row_dict = dict(row)
        token = row_dict.get("token")
        if token:
            row_dict["token"] = token[:6] + "..." + token[-6:] if len(token) > 12 else "..."
        cert = row_dict.get("certificate_content")
        if cert:
            row_dict["certificate_content"] = cert[:30] + "..." + cert[-30:] if len(cert) > 60 else "..."
        print(row_dict)
