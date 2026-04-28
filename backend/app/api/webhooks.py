from fastapi import APIRouter, Depends, HTTPException, Header, Request, BackgroundTasks
from sqlmodel import Session, select
from app.core.database import get_session, SessionLocal
from app.models import IikoSettings, IikoWebhookEvent
from app.services.iiko_sync_service import iiko_sync_service
import logging

router = APIRouter()
logger = logging.getLogger(__name__)


async def run_sync_with_session(sync_method, *args, **kwargs):
    """Хелпер для запуска фоновых задач с новой сессией БД"""
    with SessionLocal() as session:
        try:
            await sync_method(session, *args, **kwargs)
        except Exception as e:
            logger.error(f"Error in background task {sync_method.__name__}: {e}")


async def process_stop_list_update():
    """Фоновая задача обновления стоп-листов"""
    await run_sync_with_session(iiko_sync_service.sync_stop_lists)


async def process_courier_assigned(event_info: dict):
    """Обновить courier_name в заказе и создать/обновить запись в courier_orders"""
    from app.models.order import Order
    from app.models.employee import Employee, CourierOrder
    from datetime import datetime, timezone
    from sqlalchemy.orm.attributes import flag_modified

    order_id = event_info.get("id") or (event_info.get("order") or {}).get("id")
    courier_info = event_info.get("courierInfo") or {}
    c_obj = courier_info.get("courier") or {}
    fn = (c_obj.get("firstName") or c_obj.get("name") or "").strip()
    ln = (c_obj.get("lastName") or "").strip()
    courier_name = f"{fn} {ln}".strip() or courier_info.get("courierName") or ""
    courier_iiko_id = c_obj.get("id")

    if not order_id or not courier_name:
        logger.warning(f"Skipping courier assignment: missing order_id or courier_name. Payload: {event_info}")
        return

    with SessionLocal() as session:
        try:
            order = session.exec(select(Order).where(Order.iiko_order_id == order_id)).first()
            if order:
                if order.courier_name != courier_name:
                    order.courier_name = courier_name
                    order.updated_at = datetime.now(timezone.utc)
                    session.add(order)

            if courier_iiko_id and order:
                emp = session.exec(select(Employee).where(Employee.iiko_id == courier_iiko_id)).first()
                if emp:
                    # Используем уникальный ключ для записи о курьере в рамках заказа
                    iiko_uid = f"wh_{order_id}"
                    existing_co = session.exec(
                        select(CourierOrder).where(CourierOrder.iiko_id == iiko_uid)
                    ).first()
                    
                    if existing_co:
                        # Если курьер изменился - обновляем запись
                        if existing_co.employee_id != emp.id:
                            logger.info(f"Updating courier for order {order_id}: {existing_co.employee_id} -> {emp.id}")
                            existing_co.employee_id = emp.id
                            existing_co.updated_at = datetime.now(timezone.utc)
                            session.add(existing_co)
                    else:
                        co = CourierOrder(
                            iiko_id=iiko_uid,
                            order_num=str(getattr(order, 'external_number', order_id) or order_id)[:20],
                            employee_id=emp.id,
                            address=getattr(order, 'delivery_address', None),
                            delivery_zone=getattr(order, 'delivery_zone', None),
                            created_at_iiko=getattr(order, 'iiko_creation_time', None) or datetime.now(timezone.utc),
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        session.add(co)

            session.commit()
            logger.info(f"Courier processed successfully: order={order_id}, courier={courier_name}")
            
            # Отправка уведомления курьеру в VK
            if order:
                try:
                    await iiko_sync_service.send_order_notification(order, "courier_assigned")
                except Exception as vk_err:
                    logger.error(f"Failed to send courier notification: {vk_err}")
        except Exception as e:
            logger.error(f"Error processing courier assigned: {e}. Payload: {event_info}")
            session.rollback()


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
    settings = session.exec(select(IikoSettings)).first()

    if settings and settings.webhook_auth_token:
        token_to_check = authorization.replace("Bearer ", "") if authorization else ""
        if token_to_check != settings.webhook_auth_token:
            masked_auth = f"{authorization[:15]}...{authorization[-4:]}" if authorization and len(authorization) > 20 else "***"
            logger.warning(f"Webhook connection attempt with invalid token: {masked_auth}")
            raise HTTPException(status_code=401, detail="Invalid Auth Token")

    try:
        payload = await request.json()
        import json
        logger.info(f"==> Incoming Webhook Payload: {json.dumps(payload, indent=2, ensure_ascii=False)}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON")

    events = payload if isinstance(payload, list) else [payload]
    processed_ids = []

    for event in events:
        event_type = event.get("eventType")
        event_id = event.get("eventId") or event.get("correlationId")

        logger.info(f"Received iiko webhook: {event_type} (ID: {event_id})")

        log_entry = IikoWebhookEvent(
            event_type=event_type or "Unknown",
            event_id=event_id or "unknown",
            payload=event,
            processed=False
        )
        session.add(log_entry)
        session.commit()
        session.refresh(log_entry)
        processed_ids.append(log_entry.id)

        if event_type == "StopListUpdate" and background_tasks:
            background_tasks.add_task(process_stop_list_update)
            log_entry.processed = True
            log_entry.error = "Background sync started"
            session.add(log_entry)
            session.commit()

        elif event_type in ["DeliveryOrderUpdate", "DeliveryOrderCreate", "DeliveryOrderStatusChanged", "CourierAssigned"]:
            event_info = event.get("eventInfo", {})
            order_data = event_info.get("order")
            order_id = event_info.get("id")

            if not order_id and order_data:
                order_id = order_data.get("id")

            org_id = event.get("organizationId")

            if order_id and org_id and background_tasks:
                # Всегда запрашиваем полные данные через API
                logger.info(f"Triggering background API sync for order {order_id} ({event_type})")
                background_tasks.add_task(run_sync_with_session, iiko_sync_service.sync_order_by_id, order_id, org_id)

                # Если это назначение курьера, дополнительно обрабатываем быстрый лог
                if event_type == "CourierAssigned":
                    background_tasks.add_task(process_courier_assigned, event_info)

                log_entry.processed = True
                log_entry.error = f"Background order sync ({event_type}) started"
                session.add(log_entry)
                session.commit()

        elif event_type in ["PersonalSessionUpdate", "CashShiftUpdate", "PersonalShift"]:
            if background_tasks:
                background_tasks.add_task(run_sync_with_session, iiko_sync_service.sync_employees_full)
                log_entry.processed = True
                log_entry.error = "Background employee sync started"
                session.add(log_entry)
                session.commit()

        elif event_type in ["CourierAssigned", "DeliveryOrderStatusChanged"]:
            # Эти события теперь обрабатываются в блоке выше вместе с DeliveryOrderUpdate
            pass

    return {"status": "ok", "ids": processed_ids}
