import sys
sys.path.insert(0, '/app')
from app.core.database import SessionLocal
from app.models.employee import Employee
from sqlmodel import select

with SessionLocal() as session:
    employees = session.exec(select(Employee)).all()
    print("Employees in DB:")
    for e in employees:
        print(f"  ID: {e.id}, Name: '{e.name}', Role: '{e.role}', IsCourier: {e.is_courier}")
