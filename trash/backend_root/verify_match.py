import sys
sys.path.insert(0, '/app')
from app.core.database import SessionLocal
from app.models.order import Order
from app.models.employee import Employee
from sqlmodel import select

with SessionLocal() as session:
    # Get all orders with courier
    orders = session.exec(select(Order).where(Order.courier_name != "Не назначен")).all()
    print(f"Orders with courier: {len(orders)}")
    for o in orders[:5]:
        print(f"Order: id={o.id}, ext_num={o.external_number}, courier={o.courier_name}")
        
    # Check if we can find these couriers in employees
    for o in orders[:5]:
        cname = o.courier_name.strip()
        emp = session.exec(select(Employee).where(Employee.name == cname)).first()
        if emp:
            print(f"  FOUND Employee: {emp.name}, role={emp.role}, is_courier={emp.is_courier}")
        else:
            print(f"  NOT FOUND Employee for '{cname}'")
