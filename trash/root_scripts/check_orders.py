from app.models import Order
from sqlmodel import Session, select, func
from app.core.database import engine

with Session(engine) as session:
    # Уникальные значения order_type
    orders = session.exec(select(Order)).all()
    types = set(o.order_type for o in orders if o.order_type)
    print(f"Order types: {sorted(types)}")
    
    # Заказы с courier_name
    with_courier = [o for o in orders if o.courier_name and o.courier_name != "Не назначен"]
    print(f"Orders with real courier: {len(with_courier)}")
    for o in with_courier[:5]:
        print(f"  courier={o.courier_name} type={o.order_type}")
    
    # Всего заказов с любым courier_name
    with_any = [o for o in orders if o.courier_name]
    print(f"Orders with any courier_name: {len(with_any)}")
