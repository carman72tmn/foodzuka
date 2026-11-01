from app.core.security import create_access_token
from app.core.database import engine
from sqlmodel import Session, select
from app.models.user import User
import httpx
import time

with Session(engine) as s:
    admin = s.exec(select(User).where(User.username == "0001")).first()
    token = create_access_token(admin.id)

headers = {"Authorization": f"Bearer {token}"}

t0 = time.time()
r = httpx.get("http://localhost:8000/api/v1/multichat/dialogs", headers=headers, timeout=10)
dt = (time.time() - t0) * 1000
data = r.json() if r.status_code == 200 else []
print(f"GET /dialogs -> Status {r.status_code}, Dialogs: {len(data)}, Time: {dt:.1f} ms")

if len(data) > 0:
    first_d = data[0]
    ch = first_d["channel"]
    pid = first_d["peer_id"]
    t1 = time.time()
    hr = httpx.get(f"http://localhost:8000/api/v1/multichat/dialogs/{ch}/{pid}/history", headers=headers, timeout=10)
    dt1 = (time.time() - t1) * 1000
    hdata = hr.json() if hr.status_code == 200 else []
    print(f"GET /dialogs/{ch}/{pid}/history ({ch}, {pid}) -> Status {hr.status_code}, Msgs: {len(hdata)}, Time: {dt1:.1f} ms")
