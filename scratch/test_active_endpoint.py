import time
import requests
from app.core.database import engine
from sqlmodel import Session, select
from app.models.user import User
from app.core.security import create_access_token

with Session(engine) as session:
    admin = session.exec(select(User).where(User.username == '0001')).first()
    token = create_access_token(admin.id)

headers = {'Authorization': f'Bearer {token}'}

print('--- ТЕСТ АКТИВНЫХ ЗАКАЗОВ (/api/v1/orders/active) ---')
for i in range(3):
    t0 = time.time()
    r = requests.get('http://127.0.0.1:8000/api/v1/orders/active', headers=headers)
    dt = (time.time() - t0) * 1000
    print(f'Запрос {i+1}: {r.status_code}, {dt:.1f} мс, заказов в работе: {len(r.json())}')

print('\n--- ТЕСТ КЭША АРХИВНЫХ ЗАКАЗОВ (/api/v1/orders/?limit=250) ---')
for i in range(2):
    t0 = time.time()
    r = requests.get('http://127.0.0.1:8000/api/v1/orders/?limit=250', headers=headers)
    dt = (time.time() - t0) * 1000
    print(f'Запрос {i+1}: {r.status_code}, {dt:.1f} мс, получено заказов: {len(r.json())}')
