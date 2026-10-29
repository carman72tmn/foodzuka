from app.core.database import engine
from sqlmodel import Session, select
from app.models.order import Order

with Session(engine) as db:
    # Обновим 1063
    o1063 = db.exec(select(Order).where(Order.id == 1063)).first()
    if o1063:
        o1063.courier_name = "Супер Администратор"
        db.add(o1063)
        print("Updated 1063")
    
    # Обновим 1068
    o1068 = db.exec(select(Order).where(Order.id == 1068)).first()
    if o1068:
        o1068.order_type = "Доставка"
        o1068.courier_name = "Супер Администратор"
        o1068.status = "delivering"
        db.add(o1068)
        print("Updated 1068")
        
    db.commit()
