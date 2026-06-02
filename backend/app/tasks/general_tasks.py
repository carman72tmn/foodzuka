"""
Общие задачи синхронизации (Меню, Заказы)
"""
import asyncio
import logging
from datetime import datetime, timezone
from sqlmodel import Session
from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.sync_log import SyncStatus
from app.services.iiko_sync_service import iiko_sync_service

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.general_tasks.sync_menu_task")
def sync_menu_task(self, status_id: int):
    """Задача синхронизации меню"""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "running"
                status.details = "Запуск синхронизации меню..."
                session.add(status)
                session.commit()

            # Выполняем синхронизацию
            res = loop.run_until_complete(iiko_sync_service.sync_menu(session))
            
            # Обновляем статус
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "completed" if res.get("success") else "error"
                status.details = res.get("message") or "Синхронизация завершена"
                status.processed_count = res.get("products_synced", 0)
                status.total_count = res.get("products_synced", 0)
                status.added_count = res.get("categories_synced", 0)
                status.updated_at = datetime.now(timezone.utc)
                session.add(status)
                session.commit()
        return res
    except Exception as e:
        logger.error(f"Menu sync task failed: {e}")
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "error"
                status.details = str(e)
                session.add(status)
                session.commit()
        raise e

@celery_app.task(bind=True, name="app.tasks.general_tasks.sync_orders_task")
def sync_orders_task(self, status_id: int, hours: int = 24):
    """Задача синхронизации заказов"""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "running"
                status.details = f"Синхронизация заказов за {hours} ч..."
                session.add(status)
                session.commit()

            # Выполняем синхронизацию
            # Метод sync_orders возвращает количество обработанных заказов
            count = loop.run_until_complete(iiko_sync_service.sync_orders(session, hours=hours))
            
            # Обновляем статус
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "completed"
                status.details = f"Синхронизировано заказов: {count}"
                status.processed_count = count
                status.total_count = count
                status.updated_at = datetime.now(timezone.utc)
                session.add(status)
                session.commit()
        return {"count": count}
    except Exception as e:
        logger.error(f"Orders sync task failed: {e}")
        with Session(engine) as session:
            status = session.get(SyncStatus, status_id)
            if status:
                status.status = "error"
                status.details = str(e)
                session.add(status)
                session.commit()
        raise e

@celery_app.task(bind=True, name="app.tasks.general_tasks.sync_courier_deliveries_task")
def sync_courier_deliveries_task(self, days: int = 1):
    """Задача синхронизации доставок курьеров из Resto OLAP"""
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    try:
        with Session(engine) as session:
            # Выполняем синхронизацию
            loop.run_until_complete(iiko_sync_service.sync_courier_deliveries(session, days=days))
        return {"status": "completed"}
    except Exception as e:
        logger.error(f"Courier deliveries sync task failed: {e}")
        raise e


@celery_app.task(name="app.tasks.general_tasks.download_product_images_task")
def download_product_images_task():
    """Фоновое скачивание изображений товаров из iiko Cloud"""
    import httpx
    from pathlib import Path
    from app.models.product import Product

    media_dir = Path("/app/media/img/products")
    media_dir.mkdir(parents=True, exist_ok=True)

    logger.info("Запуск задачи скачивания изображений товаров...")
    downloaded_count = 0
    failed_count = 0

    try:
        with Session(engine) as session:
            # Выбираем товары с внешними ссылками на картинки
            products = session.query(Product).filter(
                Product.image_url.like("http%")
            ).all()

            if not products:
                logger.info("Нет новых изображений для скачивания.")
                return {"status": "success", "message": "Нет новых изображений для скачивания", "count": 0}

            logger.info(f"Найдено {len(products)} товаров для скачивания картинок.")
            
            with httpx.Client(timeout=15.0, follow_redirects=True) as client:
                for prod in products:
                    ext_url = prod.image_url
                    if not ext_url:
                        continue

                    # Определяем расширение файла
                    ext = Path(ext_url).suffix or ".png"
                    if "?" in ext:
                        ext = ext.split("?")[0]
                    # Ограничиваем длину расширения на случай странных URL
                    if len(ext) > 5:
                        ext = ".png"

                    local_filename = f"{prod.iiko_id}{ext}"
                    local_path = media_dir / local_filename

                    try:
                        response = client.get(ext_url)
                        if response.status_code == 200:
                            with open(local_path, "wb") as f:
                                f.write(response.content)
                            
                            # Обновляем путь в БД на локальный относительный путь
                            prod.image_url = f"/media/img/products/{local_filename}"
                            session.add(prod)
                            downloaded_count += 1
                        else:
                            logger.warning(f"Не удалось скачать {ext_url}, статус-код: {response.status_code}")
                            failed_count += 1
                    except Exception as download_err:
                        logger.error(f"Ошибка при скачивании {ext_url}: {download_err}")
                        failed_count += 1

            session.commit()
            
        msg = f"Успешно скачано {downloaded_count} изображений, не удалось: {failed_count}"
        logger.info(msg)
        return {"status": "success", "message": msg, "downloaded": downloaded_count, "failed": failed_count}

    except Exception as e:
        logger.error(f"Критическая ошибка в задаче скачивания изображений: {e}", exc_info=True)
        raise e

