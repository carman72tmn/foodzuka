from fastapi import APIRouter, Depends, HTTPException, Header, Request, BackgroundTasks
from sqlmodel import Session, select
from app.core.database import get_session
from app.models import IikoSettings, IikoWebhookEvent
from app.services.iiko_sync_service import iiko_sync_service
import logging
import json

router = APIRouter()
logger = logging.getLogger(__name__)

async def process_stop_list_update():
    """Фоновая задача обновления стоп-листов"""
    try:
        logger.info("Вебхук: запуск синхронизации стоп-листов")
        await iiko_sync_service.sync_stop_lists()
    except Exception as e:
        logger.error(f"Ошибка фоновой синхронизации стоп-листов: {e}")

async def handle_single_event(event: dict, session: Session, background_tasks: BackgroundTasks):
    """Обработка одного события из вебхука"""
    event_type = event.get("eventType")
    event_id = event.get("eventId") or event.get("correlationId")
    org_id = event.get("organizationId")

    logger.info(f"Обработка события iiko: {event_type} (ID: {event_id}, Org: {org_id})")

    # Логирование события в БД
    log_entry = IikoWebhookEvent(
        event_type=event_type or "Unknown",
        event_id=str(event_id) if event_id else "unknown",
        payload=event,
        processed=False
    )
    session.add(log_entry)
    session.commit()
    session.refresh(log_entry)

    try:
        if event_type == "StopListUpdate" and background_tasks:
            background_tasks.add_task(process_stop_list_update)
            log_entry.processed = True
            log_entry.error = "Синхронизация стоп-листа запущена"
        
        elif event_type == "DeliveryOrderUpdate":
            order_id = event.get("eventInfo", {}).get("id")
            if order_id and org_id and background_tasks:
                background_tasks.add_task(iiko_sync_service.sync_order_by_id, session, order_id, org_id)
                log_entry.processed = True
                log_entry.error = "Синхронизация заказа запущена"
        
        elif event_type in ["PersonalSessionUpdate", "CashShiftUpdate"]:
            if background_tasks:
                background_tasks.add_task(iiko_sync_service.sync_employees_full, session)
                log_entry.processed = True
                log_entry.error = "Синхронизация сотрудников запущена"
        
        session.add(log_entry)
        session.commit()
    except Exception as e:
        logger.error(f"Ошибка при обработке события {event_type}: {e}")
        log_entry.error = str(e)
        session.add(log_entry)
        session.commit()

    return log_entry.id

@router.get("/test")
async def test_webhook_route():
    return {"message": "Обработчик вебхуков активен"}

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
    # 1. Проверка настроек и авторизации
    settings = session.exec(select(IikoSettings)).first()
    
    if settings and settings.webhook_auth_token:
        # Стрипаем 'Bearer ' если есть
        auth_header = authorization or ""
        token_to_check = auth_header.replace("Bearer ", "").strip()
        if token_to_check != settings.webhook_auth_token:
            logger.warning(f"Попытка вызова вебхука с неверным токеном: {token_to_check}")
            raise HTTPException(status_code=401, detail="Неверный токен авторизации")
    
    # 2. Чтение тела запроса
    try:
        payload = await request.json()
    except Exception:
        raise HTTPException(status_code=400, detail="Некорректный JSON")

    # iiko может прислать как один объект, так и список объектов
    events = payload if isinstance(payload, list) else [payload]
    
    processed_ids = []
    for event in events:
        eid = await handle_single_event(event, session, background_tasks)
        processed_ids.append(eid)

    return {"status": "ok", "processed_events": len(events), "ids": processed_ids}
