from fastapi import APIRouter, Depends, HTTPException, Header, Request, BackgroundTasks
from sqlmodel import Session, select
from app.core.database import get_session
from app.models import IikoSettings, IikoWebhookEvent
from app.services.iiko_sync_service import iiko_sync_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

async def process_stop_list_update():
    """Фоновая задача обновления стоп-листов"""
    try:
        logger.info("Webhook triggered stop-list sync")
        await iiko_sync_service.sync_stop_lists()
    except Exception as e:
        logger.error(f"Error in background stop-list sync: {e}")

@router.get("/test")
async def test_webhook_route():
    return {"message": "Webhook router is working"}

@router.post("/iiko")
async def iiko_webhook(
    request: Request,
    authorization: str = Header(None),
    session: Session = Depends(get_session),
    background_tasks: BackgroundTasks = None
):
    """
    Прием вебхуков от iiko Cloud API
    URL: /api/v1/webhooks/iiko
    """
    # 1. Получаем настройки
    settings = session.exec(select(IikoSettings)).first()
    
    # 2. Проверка авторизации
    # Если токен задан в настройках, он должен совпадать
    if settings and settings.webhook_auth_token:
        # iiko может присылать "Bearer <token>" или просто токен? 
        # Обычно это просто строка, но проверим, не нужно ли стрипать Bearer
        token_to_check = authorization.replace("Bearer ", "") if authorization else ""
        if token_to_check != settings.webhook_auth_token:
            logger.warning(f"Webhook connection attempt with invalid token: {authorization}")
            raise HTTPException(status_code=401, detail="Invalid Auth Token")
    
    # 3. Чтение тела запроса
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    event_type = payload.get("eventType")
    event_id = payload.get("eventId") or payload.get("correlationId")

    logger.info(f"Received iiko webhook: {event_type} (ID: {event_id})")

    # 4. Логирование события в БД
    log_entry = IikoWebhookEvent(
        event_type=event_type or "Unknown",
        event_id=event_id or "unknown",
        payload=payload,
        processed=False
    )
    session.add(log_entry)
    session.commit()
    session.refresh(log_entry)

    # 5. Реакция на события
    if event_type == "StopListUpdate" and background_tasks:
        background_tasks.add_task(process_stop_list_update)
        log_entry.processed = True
        log_entry.error = "Background sync started"
        session.add(log_entry)
        session.commit()

    elif event_type == "DeliveryOrderUpdate":
        # Синхронизация конкретного заказа при его обновлении
        order_id = payload.get("eventInfo", {}).get("id")
        org_id = payload.get("organizationId")
        if order_id and org_id and background_tasks:
            background_tasks.add_task(iiko_sync_service.sync_order_by_id, session, order_id, org_id)
            log_entry.processed = True
            log_entry.error = "Background order sync started"
            session.add(log_entry)
            session.commit()

    elif event_type in ["PersonalSessionUpdate", "CashShiftUpdate"]:
        # Триггер полной синхронизации сотрудников при открытии/закрытии смен
        if background_tasks:
            background_tasks.add_task(iiko_sync_service.sync_employees_full, session)
            log_entry.processed = True
            log_entry.error = "Background employee sync started"
            session.add(log_entry)
            session.commit()

    return {"status": "ok", "id": log_entry.id}
