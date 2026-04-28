import os
import sys
import asyncio
from datetime import datetime
from decimal import Decimal
from sqlalchemy import cast, String

# Добавляем путь к приложению
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.database import get_session
from app.models import Order, IikoWebhookEvent, OrderStatus
from app.services.iiko_sync_service import iiko_sync_service
from sqlmodel import Session, select, create_engine
from app.core.config import settings

async def fix_orders():
    # Используем асинхронный движок или просто сессию через SQLModel
    engine = create_engine(str(settings.DATABASE_URL))
    
    with Session(engine) as session:
        # 1. Находим последние 50 заказов для принудительного обновления адресов и номеров
        statement = select(Order).order_by(Order.created_at.desc()).limit(50)
        
        orders = session.exec(statement).all()
        print(f"Checking {len(orders)} recent orders...")
        
        fixed_count = 0
        for order in orders:
            # 2. Ищем событие вебхука для этого заказа
            # Фильтруем за последние 7 дней для скорости
            webhook_stmt = select(IikoWebhookEvent).where(
                IikoWebhookEvent.event_type == "DeliveryOrderUpdate",
                cast(IikoWebhookEvent.payload, String).contains(order.iiko_order_id)
            ).order_by(IikoWebhookEvent.created_at.desc())
            
            event = session.exec(webhook_stmt).first()
            
            if event and event.payload:
                try:
                    event_info = event.payload.get("eventInfo", {})
                    org_id = event.payload.get("organizationId")
                    
                    if event_info and org_id:
                        print(f"Fixing order {order.id} (iiko_id: {order.iiko_order_id}) from event {event.id}")
                        
                        # Вызываем асинхронный метод
                        await iiko_sync_service.process_iiko_order(session, event_info, org_id)
                        
                        session.commit()
                        fixed_count += 1
                    else:
                        print(f"Skipping order {order.id}: missing event_info or org_id in payload")
                except Exception as e:
                    print(f"Error fixing order {order.id}: {str(e)}")
                    session.rollback()
            else:
                print(f"No webhook event found for order {order.id} / {order.iiko_order_id}")
        
        print(f"Successfully processed {fixed_count} orders.")

if __name__ == "__main__":
    asyncio.run(fix_orders())
