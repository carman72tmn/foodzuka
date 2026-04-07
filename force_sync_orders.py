import asyncio
from sqlmodel import Session, select
from app.core.database import engine
from app.models.order import Order
from app.services.iiko_sync_service import IikoSyncService
from app.models.iiko_settings import IikoSettings

async def force_sync_all():
    sync_service = IikoSyncService()
    
    with Session(engine) as session:
        # Получаем организацию
        settings = session.exec(select(IikoSettings)).first()
        if not settings or not settings.organization_id:
            print("Ошибка: Настройки iiko не найдены")
            return
            
        organization_id = settings.organization_id
        
        # Получаем все заказы, у которых есть iiko_order_id
        orders = session.exec(select(Order).where(Order.iiko_order_id != None)).all()
        print(f"Найдено {len(orders)} заказов для синхронизации")
        
        for order in orders:
            print(f"Синхронизация заказа {order.id} (iiko: {order.iiko_order_id})...")
            try:
                success = await sync_service.sync_order_by_id(session, order.iiko_order_id, organization_id)
                if success:
                    print(f"  Успешно: {order.terminal_group_name or 'Касса не определена'}")
                else:
                    print(f"  Ошибка: заказ не найден в iiko")
            except Exception as e:
                print(f"  Критическая ошибка: {e}")
                
        session.commit()
    print("Принудительная синхронизация завершена")

if __name__ == "__main__":
    asyncio.run(force_sync_all())
