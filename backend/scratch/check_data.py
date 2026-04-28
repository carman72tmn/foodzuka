from app.core.database import SessionLocal
from app.models.employee import Employee
from app.models.iiko_settings import IikoSettings
from sqlmodel import select

with SessionLocal() as session:
    emps = session.exec(select(Employee).where(Employee.name.ilike("%владислав%"))).all()
    print(f"Found {len(emps)} employees:")
    for e in emps:
        print(f"ID: {e.id}, Name: {e.name}, Courier: {e.is_courier}")
    
    settings = session.exec(select(IikoSettings)).first()
    if settings:
        print(f"Address format: {settings.address_format}")
        print(f"Resto URL: {settings.resto_url}")
        print(f"Resto Login: {settings.resto_login}")
