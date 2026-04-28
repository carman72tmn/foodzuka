import asyncio
import logging
from datetime import datetime, timedelta
from sqlmodel import Session, select
from app.core.database import engine
from app.services.iiko_service import iiko_service
from app.services.iiko_sync_service import iiko_sync_service
from app.models.iiko_settings import IikoSettings

# Настройка логов
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("sync_12h")

async def sync_last_12h():
    """
    Синхронизация заказов за последние 12 часов из iiko Cloud и iiko Resto (RMS).
    """
    with Session(engine) as session:
        # 1. Получаем настройки iiko
        settings = session.exec(select(IikoSettings)).first()
        if not settings or not settings.organization_id:
            logger.error("Iiko settings not found in database")
            return
            
        org_id = settings.organization_id
        api_login = settings.api_login
        
        # 2. Определяем временной интервал
        # iiko Cloud/RMS обычно работают по локальному времени (Тюмень = UTC+5)
        # Для надежности берем последние 24 часа
        now = datetime.utcnow() + timedelta(hours=5) 
        date_from = now - timedelta(hours=24)
        date_to = now + timedelta(hours=2)
        
        logger.info(f"Syncing orders from {date_from} to {date_to}")
        
        # 3. Получаем список заказов из iiko Cloud
        cloud_order_ids = set()
        try:
            logger.info("Fetching orders from iiko Cloud (by date/status)...")
            cloud_orders = await iiko_service.get_orders_by_date(
                date_from=date_from,
                date_to=date_to,
                organization_id=org_id,
                api_login=api_login
            )
            if not cloud_orders:
                logger.info("iiko Cloud returned no orders for this period.")
            for order in cloud_orders:
                if order.get("id"):
                    cloud_order_ids.add(order["id"])
            logger.info(f"Found {len(cloud_order_ids)} orders in iiko Cloud")
        except Exception as e:
            logger.error(f"Error fetching from Cloud: {e}")

        # 4. Получаем список заказов из iiko Resto (RMS)
        resto_order_ids = set()
        if settings.resto_url and settings.resto_login:
            try:
                logger.info("Fetching orders from iiko Resto (Delivery History API)...")
                resto_order_ids_list = await iiko_service.get_resto_delivery_history(
                    date_from=date_from,
                    date_to=date_to,
                    resto_url=settings.resto_url,
                    resto_login=settings.resto_login,
                    resto_password=settings.resto_password
                )
                for oid in resto_order_ids_list:
                    resto_order_ids.add(oid)
                logger.info(f"Found {len(resto_order_ids)} orders in iiko Resto")
            except Exception as e:
                logger.error(f"Error fetching from Resto: {e}")

        # 5. Объединяем ID
        all_ids = cloud_order_ids.union(resto_order_ids)
        logger.info(f"Total unique orders to sync: {len(all_ids)}")
        
        # 6. Запускаем синхронизацию для каждого заказа
        synced_count = 0
        failed_count = 0
        
        for order_id in all_ids:
            try:
                # sync_order_by_id принимает session, order_id, organization_id
                success = await iiko_sync_service.sync_order_by_id(session, order_id, org_id)
                if success:
                    synced_count += 1
                else:
                    logger.warning(f"Failed to sync order {order_id}")
                    failed_count += 1
            except Exception as e:
                logger.error(f"Error syncing order {order_id}: {e}")
                failed_count += 1
                
        session.commit()
        logger.info(f"Sync completed. Success: {synced_count}, Failed: {failed_count}")

if __name__ == "__main__":
    asyncio.run(sync_last_12h())
