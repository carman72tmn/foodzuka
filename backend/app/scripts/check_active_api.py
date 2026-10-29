from app.core.database import engine
from sqlmodel import Session, select
from app.models.order import Order, OrderStatus
from app.models.user import User

with Session(engine) as db:
    query = select(Order).where(Order.order_type == "Доставка")
    query = query.where(Order.status.in_([
        OrderStatus.new, 
        OrderStatus.confirmed, 
        OrderStatus.preparing, 
        OrderStatus.cooking, 
        OrderStatus.ready, 
        OrderStatus.delivering,
        OrderStatus.ready_for_pickup
    ]))
    
    # Сверим, сколько заказов
    orders = db.exec(query).all()
    print("Total active delivery orders in DB:", len(orders))
    for o in orders:
        print(f"Order #{o.id}: status={o.status}, courier={o.courier_name}, type={o.order_type}")
