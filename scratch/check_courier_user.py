from app.core.database import engine
from sqlmodel import Session, select
from app.models.user import User
from app.models.employee import Employee
with Session(engine) as s:
    users = s.exec(select(User).where(User.username.in_(['0001', 'courier', 'sergey']))).all()
    for u in users:
        print('USER:', u.id, u.username, u.full_name, 'iiko_id:', u.iiko_id, type(u.iiko_id))
    emps = s.exec(select(Employee).where(Employee.name.like('%Сергей%'))).all()
    for e in emps:
        print('EMP:', e.id, e.name, 'iiko_id:', e.iiko_id, type(e.iiko_id))
