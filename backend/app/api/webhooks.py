from fastapi import APIRouter, Depends, HTTPException, Header, Request, BackgroundTasks
from sqlmodel import Session, select
from app.core.database import get_session, SessionLocal
from app.models import IikoSettings, IikoWebhookEvent, SenlerSettings, SenlerSubscriber
from app.services.iiko_sync_service import iiko_sync_service
import logging
from typing import Optional

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
    """Обновить courier_name в заказе, сбросить статус подтверждения при переназначении, уведомить курьеров и сотрудников"""
    import json
    from app.models.order import Order
    from app.models.employee import Employee, CourierOrder
    from app.models.user import User
    from app.api.chat import manager
    from datetime import datetime, timezone
    from sqlalchemy.orm.attributes import flag_modified

    order_id = event_info.get("id") or (event_info.get("order") or {}).get("id")
    courier_info = event_info.get("courierInfo") or (event_info.get("order") or {}).get("courierInfo") or {}
    c_obj = courier_info.get("courier") or {} if isinstance(courier_info, dict) else {}
    
    courier_iiko_id = c_obj.get("id") if isinstance(c_obj, dict) else None
    fn = (c_obj.get("firstName") or c_obj.get("name") or "").strip() if isinstance(c_obj, dict) else ""
    ln = (c_obj.get("lastName") or "").strip() if isinstance(c_obj, dict) else ""
    courier_name = f"{fn} {ln}".strip() or (courier_info.get("courierName") if isinstance(courier_info, dict) else "") or ""
    courier_name = courier_name.replace(" None", "").strip()

    if not order_id:
        logger.warning(f"Skipping courier assignment: missing order_id. Payload: {event_info}")
        return

    with SessionLocal() as session:
        try:
            order = session.exec(select(Order).where(Order.iiko_order_id == order_id)).first()
            if not order:
                logger.warning(f"Order {order_id} not found in DB during courier assignment. Payload: {event_info}")
                return

            emp = None
            if courier_iiko_id:
                emp = session.exec(select(Employee).where(Employee.iiko_id == str(courier_iiko_id))).first()
            if not emp and courier_name:
                emp = session.exec(select(Employee).where(Employee.name == courier_name)).first()
                if not emp:
                    # Поиск по вхождению слов имени
                    target_words = {w for w in courier_name.lower().split() if len(w) > 2 and w not in ["курьер", "courier"]}
                    if target_words:
                        all_emps = session.exec(select(Employee)).all()
                        for e_item in all_emps:
                            e_words = {w for w in (e_item.name or "").lower().split() if len(w) > 2}
                            if target_words & e_words:
                                emp = e_item
                                break

            # Если сотрудник найден в справочнике, берем его официальное имя
            canonical_courier_name = emp.name if emp else (courier_name or "Не назначен")
            old_courier = order.courier_name or "Не назначен"
            is_courier_changed = (old_courier != canonical_courier_name)
            is_reassigned = bool(old_courier != "Не назначен" and canonical_courier_name != "Не назначен" and is_courier_changed)
            is_unassigned = bool(old_courier != "Не назначен" and canonical_courier_name == "Не назначен")
            is_assigned = bool(canonical_courier_name != "Не назначен")

            ext_num = str(getattr(order, 'external_number', order.id) or order.id)

            # Проверяем, не является ли заказ уже закрытым/доставленным/отмененным
            is_order_finished = bool(
                str(getattr(order, 'status', '')).lower() in ("closed", "cancelled", "delivered", "доставлен", "закрыт", "отменен") or
                getattr(order, 'is_closed', False)
            )

            if is_courier_changed:
                logger.info(f"Order #{ext_num} courier changed: '{old_courier}' -> '{canonical_courier_name}' (reassigned={is_reassigned}, unassigned={is_unassigned}, finished={is_order_finished})")
                order.courier_name = canonical_courier_name
                order.updated_at = datetime.now(timezone.utc)
                
                # При смене курьера сбрасываем статус подтверждения (если заказ еще активен)
                if not is_order_finished:
                    order.courier_notification_status = None
                    order.courier_accepted_at = None
                    order.courier_accepted_source = None
                    order.courier_read_at = None
                session.add(order)

                # Обновление записи в CourierOrder
                iiko_uid = f"wh_{order_id}"
                existing_co = session.exec(select(CourierOrder).where(CourierOrder.iiko_id == iiko_uid)).first()
                if emp:
                    if existing_co:
                        if existing_co.employee_id != emp.id:
                            logger.info(f"Updating CourierOrder for order {order_id}: {existing_co.employee_id} -> {emp.id}")
                            existing_co.employee_id = emp.id
                            existing_co.updated_at = datetime.now(timezone.utc)
                            session.add(existing_co)
                    else:
                        co = CourierOrder(
                            iiko_id=iiko_uid,
                            order_num=ext_num[:20],
                            employee_id=emp.id,
                            address=getattr(order, 'delivery_address', None),
                            delivery_zone=getattr(order, 'delivery_zone', None),
                            created_at_iiko=getattr(order, 'iiko_creation_time', None) or datetime.now(timezone.utc),
                            created_at=datetime.now(timezone.utc),
                            updated_at=datetime.now(timezone.utc)
                        )
                        session.add(co)
                elif is_unassigned and existing_co:
                    session.delete(existing_co)

                session.commit()
                session.refresh(order)

                # Если заказ уже доставлен, закрыт или отменен - блокируем отправку повторных пушей и уведомлений
                if is_order_finished:
                    logger.info(f"Order #{ext_num}: courier assignment notifications suppressed because order status is terminal '{order.status}'")
                    return

                # 1. WebSocket Broadcast в админку (/orders) и панель курьера (/pers/courier)
                now_ts = int(datetime.now(timezone.utc).timestamp() * 1000)
                ws_order_changed = {
                    "type": "order_changed",
                    "order_id": order.id,
                    "order_number": ext_num,
                    "status": order.status,
                    "customer_name": order.customer_name or "Гость",
                    "order_type": order.order_type,
                    "courier_name": order.courier_name,
                    "courier_notification_status": None,
                    "timestamp": now_ts
                }
                ws_courier_status = {
                    "type": "courier_status_changed",
                    "order_id": order.id,
                    "order_num": ext_num,
                    "courier_name": order.courier_name,
                    "courier_notification_status": None,
                    "status": "reassigned" if is_reassigned else ("unassigned" if is_unassigned else "assigned"),
                    "timestamp": now_ts
                }
                try:
                    await manager.broadcast(ws_order_changed)
                    await manager.broadcast(ws_courier_status)
                except Exception as ws_err:
                    logger.warning(f"Failed to broadcast websocket on courier change: {ws_err}")

                # 2. Персональные WebSocket и Push новому курьеру
                courier_user = None
                if emp and emp.iiko_id:
                    courier_user = session.exec(select(User).where(User.iiko_id == str(emp.iiko_id))).first()
                if not courier_user and canonical_courier_name != "Не назначен":
                    courier_user = session.exec(select(User).where(User.full_name == canonical_courier_name)).first()

                if courier_user:
                    try:
                        ws_assigned = {
                            "type": "delivery_assigned",
                            "order_id": order.id,
                            "order_number": ext_num,
                            "address": order.delivery_address,
                            "amount": float(order.total_with_discount or order.total_amount or 0),
                            "target_user_id": courier_user.id
                        }
                        await manager.send_personal_message(json.dumps(ws_assigned), courier_user.id)
                        # Push отправляется через send_courier_notification (без дублирования через send_admin_push_notification)
                        await iiko_sync_service.send_courier_notification(
                            session=session,
                            courier_user_id=courier_user.id,
                            event_type="courier_order_assigned",
                            title="Назначен заказ на доставку",
                            body=f"Заказ #{ext_num} на сумму {order.total_with_discount or order.total_amount} ₽. Адрес: {order.delivery_address}",
                            order_id=order.id,
                            order_number=ext_num,
                            extra_data={"order_id": order.id, "order_number": ext_num, "amount": float(order.total_with_discount or order.total_amount or 0), "address": order.delivery_address},
                            order=order
                        )
                    except Exception as c_err:
                        logger.error(f"Error notifying new courier user: {c_err}")

                # 3. Персональные WebSocket и Push старому курьеру о снятии
                if is_reassigned or is_unassigned:
                    try:
                        old_emp = session.exec(select(Employee).where(Employee.name == old_courier)).first()
                        old_user = None
                        if old_emp and old_emp.iiko_id:
                            old_user = session.exec(select(User).where(User.iiko_id == str(old_emp.iiko_id))).first()
                        if not old_user and old_courier != "Не назначен":
                            old_user = session.exec(select(User).where(User.full_name == old_courier)).first()

                        if old_user:
                            ws_unassigned = {
                                "type": "delivery_unassigned",
                                "order_id": order.id,
                                "order_number": ext_num,
                                "total_sum": float(order.total_with_discount or order.total_amount or 0),
                                "address": order.delivery_address,
                                "customer_name": order.customer_name or "Гость"
                            }
                            await manager.send_personal_message(json.dumps(ws_unassigned), old_user.id)
                            # Push отправляется через send_courier_notification (без дублирования через send_admin_push_notification)
                            await iiko_sync_service.send_courier_notification(
                                session=session,
                                courier_user_id=old_user.id,
                                event_type="courier_unassigned",
                                title="Заказ снят с доставки",
                                body=f"Заказ #{ext_num} передан другому курьеру или отменен",
                                order_id=order.id,
                                order_number=ext_num,
                                extra_data={"order_id": order.id, "order_number": ext_num}
                            )
                    except Exception as un_err:
                        logger.error(f"Error notifying old courier user: {un_err}")

                # 4. Системные уведомления (VK / TG / MAX) курьерам и сотрудникам
                if is_assigned:
                    try:
                        await iiko_sync_service.send_order_notification(
                            order,
                            "courier_assigned",
                            session=session,
                            is_reassigned=is_reassigned,
                            old_courier=old_courier,
                            new_courier=canonical_courier_name
                        )
                        # При переназначении курьера повторно отправляем карточку заказа новому курьеру
                        if is_reassigned:
                            logger.info(f"Order #{ext_num} re-sending order_new to new courier '{canonical_courier_name}'")
                            await iiko_sync_service.send_order_notification(
                                order,
                                "order_new",
                                session=session,
                                is_reassigned=True,
                                old_courier=old_courier,
                                new_courier=canonical_courier_name
                            )
                    except Exception as vk_err:
                        logger.error(f"Failed to send courier notifications: {vk_err}")
            else:
                logger.info(f"Courier unchanged for order #{ext_num}: '{canonical_courier_name}'")

        except Exception as e:
            logger.error(f"Error processing courier assigned: {e}. Payload: {event_info}", exc_info=True)
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
                # Если в вебхуке уже есть полный объект заказа, обрабатываем его напрямую за 0 мс без риска таймаута /by_id
                if order_data and isinstance(order_data, dict) and order_data.get("status"):
                    logger.info(f"Processing webhook payload directly for order {order_id} ({event_type})")
                    background_tasks.add_task(run_sync_with_session, iiko_sync_service.process_iiko_order, event_info, org_id)
                else:
                    logger.info(f"Triggering background API sync for order {order_id} ({event_type})")
                    background_tasks.add_task(run_sync_with_session, iiko_sync_service.sync_order_by_id, order_id, org_id)

                # Если это назначение курьера или обновление заказа с информацией о курьере, запускаем быстрый процессинг
                has_courier_info = bool(
                    event_info.get("courierInfo") or 
                    (order_data and isinstance(order_data, dict) and order_data.get("courierInfo"))
                )
                if event_type == "CourierAssigned" or has_courier_info:
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


@router.post("/senler")
async def senler_webhook(
    request: Request,
    secret: Optional[str] = None,
    session: Session = Depends(get_session)
):
    """
    Прием вебхуков от сервиса рассылок Senler
    URL: /api/v1/webhooks/senler
    """
    settings = session.exec(select(SenlerSettings)).first()
    if not settings or not settings.is_active:
        logger.warning("Senler webhook received but integration is inactive or not configured")
        raise HTTPException(status_code=400, detail="Senler integration inactive")

    # Проверка секретного ключа
    if settings.secret_key and secret != settings.secret_key:
        logger.warning(f"Senler webhook unauthorized attempt: invalid secret '{secret}'")
        raise HTTPException(status_code=401, detail="Invalid secret key")

    try:
        payload = await request.json()
        logger.info(f"Incoming Senler Webhook Payload: {payload}")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid JSON payload")

    # Парсинг полей из payload Senler
    # Структура по умолчанию в Senler содержит: action/event, user_id/vk_user_id, subscription_id
    vk_user_id = payload.get("vk_user_id") or payload.get("user_id") or (payload.get("object", {})).get("vk_user_id")
    if not vk_user_id:
        logger.warning(f"Senler webhook skipped: vk_user_id not found in payload: {payload}")
        return {"status": "ignored", "reason": "vk_user_id_missing"}

    # Преобразуем vk_user_id в int
    try:
        vk_user_id = int(vk_user_id)
    except (ValueError, TypeError):
        logger.warning(f"Senler webhook: invalid vk_user_id format '{vk_user_id}'")
        return {"status": "error", "reason": "invalid_vk_user_id_format"}

    action = payload.get("action") or payload.get("event") or (payload.get("object", {})).get("action")
    subscription_id = payload.get("subscription_id") or (payload.get("object", {})).get("subscription_id")
    
    first_name = payload.get("first_name") or (payload.get("object", {})).get("first_name")
    last_name = payload.get("last_name") or (payload.get("object", {})).get("last_name")
    
    utm_tags = payload.get("utms") or payload.get("utm") or (payload.get("object", {}).get("utms")) or {}
    user_vars = payload.get("vars") or (payload.get("object", {}).get("vars")) or {}

    # Поиск существующего подписчика
    statement = select(SenlerSubscriber).where(SenlerSubscriber.vk_user_id == vk_user_id)
    subscriber = session.exec(statement).first()

    from app.core.datetime_utils import utc_now
    now = utc_now()

    if action in ["subscribe", "subscription_add", "user_add"]:
        # Логика подписки
        group_ids = []
        if subscriber and subscriber.group_ids:
            group_ids = list(subscriber.group_ids)
            
        if subscription_id is not None:
            try:
                sub_id = int(subscription_id)
                if sub_id not in group_ids:
                    group_ids.append(sub_id)
            except (ValueError, TypeError):
                pass
                
        if not subscriber:
            subscriber = SenlerSubscriber(
                vk_user_id=vk_user_id,
                first_name=first_name,
                last_name=last_name,
                is_subscribed=True,
                subscribe_date=now,
                group_ids=group_ids,
                utm_tags=utm_tags,
                user_vars=user_vars
            )
        else:
            subscriber.is_subscribed = True
            subscriber.subscribe_date = now
            subscriber.unsubscribe_date = None
            subscriber.group_ids = group_ids
            if first_name:
                subscriber.first_name = first_name
            if last_name:
                subscriber.last_name = last_name
            if utm_tags:
                subscriber.utm_tags = utm_tags
            if user_vars:
                subscriber.user_vars = user_vars
            subscriber.updated_at = now
            
        session.add(subscriber)
        logger.info(f"Senler Webhook: Subscriber {vk_user_id} subscribed to group {subscription_id}")

    elif action in ["unsubscribe", "subscription_remove", "user_remove"]:
        # Логика отписки
        if subscriber:
            group_ids = list(subscriber.group_ids) if subscriber.group_ids else []
            if subscription_id is not None:
                try:
                    sub_id = int(subscription_id)
                    if sub_id in group_ids:
                        group_ids.remove(sub_id)
                except (ValueError, TypeError):
                    pass
            
            subscriber.group_ids = group_ids
            
            # Если отписался от конкретной группы, но состоит в других, он все еще активный подписчик.
            # Если отписался от всего или групп не осталось:
            if not group_ids or subscription_id is None:
                subscriber.is_subscribed = False
                subscriber.unsubscribe_date = now
                logger.info(f"Senler Webhook: Subscriber {vk_user_id} unsubscribed completely")
            else:
                logger.info(f"Senler Webhook: Subscriber {vk_user_id} unsubscribed from group {subscription_id}, remains in {group_ids}")
                
            subscriber.updated_at = now
            session.add(subscriber)
        else:
            logger.info(f"Senler Webhook: Unsubscribe received for unknown subscriber {vk_user_id}, ignoring")

    session.commit()
    return {"status": "ok"}
