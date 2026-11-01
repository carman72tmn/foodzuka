import asyncio
from sqlmodel import select
from app.core.database import SessionLocal
from app.models.order import Order
from app.models.iiko_settings import IikoSettings
from app.services.iiko_sync_service import IikoSyncService

async def main():
    session = SessionLocal()
    try:
        settings_db = session.exec(select(IikoSettings)).first()
        org_id = settings_db.organization_id if settings_db else None
        if not org_id:
            print("Error: organization_id not found")
            return
            
        sync_service = IikoSyncService()
        orders = session.query(Order).order_by(Order.id.desc()).limit(10).all()
        for o in orders:
            if o.iiko_order_id:
                print(f"Syncing order {o.id} (Num: {o.external_number})...")
                try:
                    # sync_order_by_id принимает session, iiko_order_id, org_id
                    res = await sync_service.sync_order_by_id(session, o.iiko_order_id, org_id)
                    print(f"  Result: {res}")
                except Exception as e:
                    print(f"  Error: {e}")
        
        # Печатаем обновленные данные
        session.expire_all()
        for o in orders:
            db_order = session.get(Order, o.id)
            print(f"Order {db_order.id} (Num: {db_order.external_number}):")
            print(f"  address_comment: {db_order.address_comment}")
            print(f"  additional_info: {db_order.additional_info}")
            print(f"  other_info: {db_order.other_info}")
            print("-" * 40)
    finally:
        session.close()

if __name__ == "__main__":
    asyncio.run(main())
