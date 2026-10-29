"""
Задачи Celery для интеграции с Senler
"""
import asyncio
import logging
from sqlmodel import Session, select
from app.core.celery_app import celery_app
from app.core.database import engine
from app.models.senler import SenlerSettings, SenlerSubscriber
from app.services.senler_service import senler_service
from datetime import datetime
from app.core.datetime_utils import utc_now

logger = logging.getLogger(__name__)

@celery_app.task(bind=True, name="app.tasks.senler_tasks.sync_senler_subscribers_task")
def sync_senler_subscribers_task(self):
    """
    Задача полной синхронизации подписчиков из Senler в локальную БД
    """
    loop = asyncio.get_event_loop()
    if loop.is_closed():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

    try:
        result = loop.run_until_complete(run_senler_sync())
        return {"status": "success", "result": result}
    except Exception as e:
        logger.error(f"Error in sync_senler_subscribers_task: {e}")
        raise e

async def run_senler_sync() -> str:
    with Session(engine) as db:
        settings = senler_service._get_settings(db)
        if not settings or not settings.is_active:
            logger.warning("Senler integration is not active, skipping sync")
            return "Skipped: Integration inactive"
        
        offset_id = None
        count = 100
        total_imported = 0
        has_more = True
        
        while has_more:
            try:
                res = await senler_service.get_subscribers(offset_id=offset_id, count=count, db=db)
                items = res.get("items", [])
                if not items:
                    break
                    
                for item in items:
                    vk_user_id = item.get("vk_user_id")
                    if not vk_user_id:
                        continue
                        
                    # Попробуем найти существующего
                    statement = select(SenlerSubscriber).where(SenlerSubscriber.vk_user_id == vk_user_id)
                    subscriber = db.exec(statement).first()
                    
                    # Парсим даты подписки
                    subscribe_date = None
                    date_str = item.get("date")
                    if date_str:
                        try:
                            # Пробуем распарсить ISO формат даты
                            subscribe_date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                        except Exception:
                            pass
                    
                    # Извлекаем группы, UTM и переменные
                    subscriptions = item.get("subscriptions", [])
                    group_ids = []
                    for sub in subscriptions:
                        if isinstance(sub, dict) and "subscription_id" in sub:
                            group_ids.append(sub["subscription_id"])
                        elif isinstance(sub, int):
                            group_ids.append(sub)
                            
                    utm_tags = item.get("utms", {})
                    user_vars = item.get("vars", {})
                    
                    if not subscriber:
                        subscriber = SenlerSubscriber(
                            vk_user_id=vk_user_id,
                            first_name=item.get("first_name"),
                            last_name=item.get("last_name"),
                            is_subscribed=True,
                            subscribe_date=subscribe_date,
                            group_ids=group_ids,
                            utm_tags=utm_tags,
                            user_vars=user_vars
                        )
                    else:
                        subscriber.first_name = item.get("first_name")
                        subscriber.last_name = item.get("last_name")
                        subscriber.is_subscribed = True
                        if subscribe_date:
                            subscriber.subscribe_date = subscribe_date
                        subscriber.group_ids = group_ids
                        subscriber.utm_tags = utm_tags
                        subscriber.user_vars = user_vars
                        subscriber.updated_at = utc_now()
                        
                    db.add(subscriber)
                    total_imported += 1
                    
                db.commit()
                
                offset_id = res.get("offset_id")
                if not offset_id or len(items) < count:
                    has_more = False
                    
                # Пауза во избежание лимитов API
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error during Senler sync batch: {e}")
                has_more = False
                raise e
                
        return f"Imported/Updated {total_imported} subscribers"
