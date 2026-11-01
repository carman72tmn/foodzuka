import sys
import os
sys.path.append('/root/foodzuka/backend')
from app.schemas import OrderResponse
from app.models.order import Order, OrderItem, OrderStatus
from sqlmodel import Session, create_engine, select
from decimal import Decimal
import json

# DB setup
DATABASE_URL = os.environ.get('DATABASE_URL', 'postgresql://user:pass@db:5432/foodzuka')
engine = create_engine(DATABASE_URL)

with Session(engine) as session:
    order = session.exec(select(Order).limit(1)).first()
    if not order:
        print('No orders found')
        sys.exit(0)
    
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    order_dict = order.model_dump()
    order_dict['items'] = [item.model_dump() for item in items]
    order_dict['resolved_delivery_zone_name'] = order.resolved_zone_name
    
    try:
        OrderResponse.model_validate(order_dict)
        print('Validation SUCCESS')
    except Exception as e:
        print('Validation FAILED')
        print(e)
