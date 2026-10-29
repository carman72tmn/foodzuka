import logging
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from pydantic import BaseModel

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.models.push_subscription import PushSubscription
from app.models.admin_notification_settings import AdminNotificationSettings
from app.models.admin_notification import AdminNotification
from app.core.webpush_utils import generate_vapid_keys, send_web_push

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/notifications", tags=["Admin Notifications"])

# --- СХЕМЫ PYDANTIC ---
class PushSubscriptionKeys(BaseModel):
    p256dh: str
    auth: str

class PushSubscriptionCreate(BaseModel):
    endpoint: str
    keys: PushSubscriptionKeys

class NotificationSettingsUpdate(BaseModel):
    new_order_sound_enabled: Optional[bool] = None
    new_order_sound_file: Optional[str] = None
    new_order_push_enabled: Optional[bool] = None
    new_order_repeat_enabled: Optional[bool] = None
    new_order_repeat_interval: Optional[int] = None
    
    new_payment_sound_enabled: Optional[bool] = None
    new_payment_sound_file: Optional[str] = None
    new_payment_push_enabled: Optional[bool] = None
    
    courier_delivery_sound_enabled: Optional[bool] = None
    courier_delivery_sound_file: Optional[str] = None
    courier_delivery_push_enabled: Optional[bool] = None
    
    chat_message_sound_enabled: Optional[bool] = None
    chat_message_sound_file: Optional[str] = None
    chat_message_push_enabled: Optional[bool] = None
    
    order_cancelled_sound_enabled: Optional[bool] = None
    order_cancelled_sound_file: Optional[str] = None
    order_cancelled_push_enabled: Optional[bool] = None
    
    order_changed_sound_enabled: Optional[bool] = None
    order_changed_sound_file: Optional[str] = None
    order_changed_push_enabled: Optional[bool] = None

    delivery_unassigned_sound_enabled: Optional[bool] = None
    delivery_unassigned_sound_file: Optional[str] = None
    delivery_unassigned_push_enabled: Optional[bool] = None
    
    delivery_assigned_sound_enabled: Optional[bool] = None
    delivery_assigned_sound_file: Optional[str] = None
    delivery_assigned_push_enabled: Optional[bool] = None
    
    change_cooking_time_sound_enabled: Optional[bool] = None
    change_cooking_time_sound_file: Optional[str] = None
    change_cooking_time_push_enabled: Optional[bool] = None
    
    change_items_sound_enabled: Optional[bool] = None
    change_items_sound_file: Optional[str] = None
    change_items_push_enabled: Optional[bool] = None
    
    change_amount_sound_enabled: Optional[bool] = None
    change_amount_sound_file: Optional[str] = None
    change_amount_push_enabled: Optional[bool] = None
    
    change_payment_sound_enabled: Optional[bool] = None
    change_payment_sound_file: Optional[str] = None
    change_payment_push_enabled: Optional[bool] = None
    
    change_address_sound_enabled: Optional[bool] = None
    change_address_sound_file: Optional[str] = None
    change_address_push_enabled: Optional[bool] = None
    order_changed_scope: Optional[str] = None

    # Персональные настройки уведомлений курьера
    courier_order_assigned_sound_enabled: Optional[bool] = None
    courier_order_assigned_sound_file: Optional[str] = None
    courier_order_assigned_push_enabled: Optional[bool] = None

    courier_cooking_time_set_sound_enabled: Optional[bool] = None
    courier_cooking_time_set_sound_file: Optional[str] = None
    courier_cooking_time_set_push_enabled: Optional[bool] = None

    courier_cooking_time_changed_sound_enabled: Optional[bool] = None
    courier_cooking_time_changed_sound_file: Optional[str] = None
    courier_cooking_time_changed_push_enabled: Optional[bool] = None

    courier_status_changed_sound_enabled: Optional[bool] = None
    courier_status_changed_sound_file: Optional[str] = None
    courier_status_changed_push_enabled: Optional[bool] = None

    courier_amount_changed_sound_enabled: Optional[bool] = None
    courier_amount_changed_sound_file: Optional[str] = None
    courier_amount_changed_push_enabled: Optional[bool] = None

    courier_address_changed_sound_enabled: Optional[bool] = None
    courier_address_changed_sound_file: Optional[str] = None
    courier_address_changed_push_enabled: Optional[bool] = None

    courier_changed_to_pickup_sound_enabled: Optional[bool] = None
    courier_changed_to_pickup_sound_file: Optional[str] = None
    courier_changed_to_pickup_push_enabled: Optional[bool] = None

    courier_removed_from_delivery_sound_enabled: Optional[bool] = None
    courier_removed_from_delivery_sound_file: Optional[str] = None
    courier_removed_from_delivery_push_enabled: Optional[bool] = None

    courier_unassigned_sound_enabled: Optional[bool] = None
    courier_unassigned_sound_file: Optional[str] = None
    courier_unassigned_push_enabled: Optional[bool] = None

    courier_delivery_time_changed_sound_enabled: Optional[bool] = None
    courier_delivery_time_changed_sound_file: Optional[str] = None
    courier_delivery_time_changed_push_enabled: Optional[bool] = None

    # Доставка заказа (для общих сотрудников)
    order_delivered_sound_enabled: Optional[bool] = None
    order_delivered_sound_file: Optional[str] = None
    order_delivered_push_enabled: Optional[bool] = None

    # Глобальные переключатели браузерных уведомлений
    disable_browser_notifications_couriers: Optional[bool] = None
    disable_browser_notifications_all: Optional[bool] = None

# Вспомогательный метод для получения глобальных VAPID ключей
def get_global_vapid_keys(db: Session) -> tuple:
    global_settings = db.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.id == 1)).first()
    if not global_settings:
        pub_key, priv_key = generate_vapid_keys()
        global_settings = AdminNotificationSettings(
            id=1,
            vapid_public_key=pub_key,
            vapid_private_key=priv_key,
            user_id=None
        )
        db.add(global_settings)
        db.commit()
        db.refresh(global_settings)
    elif not global_settings.vapid_public_key or not global_settings.vapid_private_key:
        pub_key, priv_key = generate_vapid_keys()
        global_settings.vapid_public_key = pub_key
        global_settings.vapid_private_key = priv_key
        db.add(global_settings)
        db.commit()
        db.refresh(global_settings)
    return global_settings.vapid_public_key, global_settings.vapid_private_key

def log_system_notification(
    db: Session,
    title: str,
    body: str,
    event_type: str,
    category: str,
    url: str = "/orders",
    subtitle: Optional[str] = None,
    badge_text: Optional[str] = None,
    badge_color: str = "primary",
    amount: Optional[float] = None,
    order_id: Optional[int] = None,
    external_key: Optional[str] = None,
    meta_json: Optional[dict] = None
):
    """Сохраняет глобальное уведомление (user_id=None) для отображения во вкладке Уведомления"""
    try:
        if external_key:
            existing = db.exec(select(AdminNotification).where(AdminNotification.external_key == external_key)).first()
            if existing:
                return existing
        notif = AdminNotification(
            user_id=None,
            title=title[:255],
            body=body[:1000] if body else "",
            url=url,
            event_type=event_type,
            category=category,
            subtitle=subtitle[:255] if subtitle else None,
            badge_text=badge_text[:64] if badge_text else None,
            badge_color=badge_color,
            amount=amount,
            order_id=order_id,
            external_key=external_key,
            meta_json=meta_json or {},
            is_read=False
        )
        db.add(notif)
        db.commit()
        db.refresh(notif)
        return notif
    except Exception as e:
        logger.error(f"Error logging system notification: {e}")
        db.rollback()
        return None


# --- ЭНДПОИНТЫ ---

@router.get("/settings")
def get_notification_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить настройки уведомлений текущего пользователя"""
    # Гарантируем наличие глобальных VAPID-ключей
    vapid_pub, vapid_priv = get_global_vapid_keys(db)
    global_settings = db.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.id == 1)).first()
    
    # Проверяем, является ли пользователь курьером
    is_courier = False
    if current_user.role and current_user.role.name and "курьер" in current_user.role.name.lower():
        is_courier = True
    elif getattr(current_user, "employee", None) and getattr(current_user.employee, "is_courier", False):
        is_courier = True

    # Ищем личные настройки пользователя
    settings_db = db.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.user_id == current_user.id)).first()
    if not settings_db:
        # Для курьеров по умолчанию выключаем общие уведомления (звуки, пуши), оставляя только курьерские
        settings_db = AdminNotificationSettings(
            user_id=current_user.id,
            vapid_public_key=vapid_pub,
            vapid_private_key=vapid_priv,
            new_order_sound_enabled=not is_courier,
            new_order_push_enabled=not is_courier,
            new_payment_sound_enabled=not is_courier,
            new_payment_push_enabled=not is_courier,
            chat_message_sound_enabled=not is_courier,
            chat_message_push_enabled=not is_courier,
            order_cancelled_sound_enabled=not is_courier,
            order_cancelled_push_enabled=not is_courier,
            delivery_unassigned_sound_enabled=not is_courier,
            delivery_unassigned_push_enabled=not is_courier,
            order_delivered_sound_enabled=not is_courier,
            order_delivered_push_enabled=not is_courier,
            order_changed_sound_enabled=False,
            order_changed_push_enabled=False,
        )
        db.add(settings_db)
        db.commit()
        db.refresh(settings_db)
    else:
        # Убеждаемся, что в личных настройках записаны актуальные VAPID-ключи
        if settings_db.vapid_public_key != vapid_pub or settings_db.vapid_private_key != vapid_priv:
            settings_db.vapid_public_key = vapid_pub
            settings_db.vapid_private_key = vapid_priv
            db.add(settings_db)
            db.commit()
            db.refresh(settings_db)

    # Транслируем глобальные мастер-переключатели из глобальной записи id=1
    if global_settings:
        settings_db.disable_browser_notifications_couriers = getattr(global_settings, "disable_browser_notifications_couriers", False)
        settings_db.disable_browser_notifications_all = getattr(global_settings, "disable_browser_notifications_all", False)
            
    return settings_db

@router.post("/settings")
def update_notification_settings(
    payload: NotificationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Обновить настройки уведомлений текущего пользователя"""
    vapid_pub, vapid_priv = get_global_vapid_keys(db)
    global_settings = db.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.id == 1)).first()
    
    settings_db = db.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.user_id == current_user.id)).first()
    if not settings_db:
        settings_db = AdminNotificationSettings(
            user_id=current_user.id,
            vapid_public_key=vapid_pub,
            vapid_private_key=vapid_priv
        )
        db.add(settings_db)
        
    update_data = payload.model_dump(exclude_unset=True)
    
    # Если переданы глобальные флаги - сохраняем их в глобальную запись id=1
    if "disable_browser_notifications_couriers" in update_data and global_settings:
        global_settings.disable_browser_notifications_couriers = update_data["disable_browser_notifications_couriers"]
        db.add(global_settings)
    if "disable_browser_notifications_all" in update_data and global_settings:
        global_settings.disable_browser_notifications_all = update_data["disable_browser_notifications_all"]
        db.add(global_settings)

    for key, value in update_data.items():
        setattr(settings_db, key, value)
        
    db.add(settings_db)
    db.commit()
    db.refresh(settings_db)
    if global_settings:
        settings_db.disable_browser_notifications_couriers = getattr(global_settings, "disable_browser_notifications_couriers", False)
        settings_db.disable_browser_notifications_all = getattr(global_settings, "disable_browser_notifications_all", False)
    return settings_db

@router.get("/vapid-public-key")
def get_vapid_public_key(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить публичный VAPID-ключ для регистрации PushSubscription во фронтенде"""
    vapid_pub, _ = get_global_vapid_keys(db)
    return {"public_key": vapid_pub}

@router.post("/subscribe")
def subscribe_push(
    payload: PushSubscriptionCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Зарегистрировать/обновить подписку браузера на пуш-уведомления для текущего пользователя"""
    existing = db.exec(select(PushSubscription).where(PushSubscription.endpoint == payload.endpoint)).first()
    if existing:
        existing.user_id = current_user.id
        existing.p256dh = payload.keys.p256dh
        existing.auth = payload.keys.auth
        db.add(existing)
        db.commit()
        return {"status": "updated", "id": existing.id}
        
    new_sub = PushSubscription(
        user_id=current_user.id,
        endpoint=payload.endpoint,
        p256dh=payload.keys.p256dh,
        auth=payload.keys.auth
    )
    db.add(new_sub)
    db.commit()
    db.refresh(new_sub)
    return {"status": "created", "id": new_sub.id}

@router.post("/unsubscribe")
def unsubscribe_push(
    payload: dict,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Удалить подписку браузера на пуш-уведомления"""
    endpoint = payload.get("endpoint")
    if not endpoint:
        raise HTTPException(status_code=400, detail="Endpoint is required")
        
    sub = db.exec(select(PushSubscription).where(PushSubscription.endpoint == endpoint)).first()
    if sub:
        db.delete(sub)
        db.commit()
        return {"status": "deleted"}
    return {"status": "not_found"}

@router.post("/test-push")
def test_push_notification(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Отправить тестовое пуш-уведомление на все устройства текущего пользователя"""
    _, vapid_priv = get_global_vapid_keys(db)
    
    subscriptions = db.exec(select(PushSubscription).where(PushSubscription.user_id == current_user.id)).all()
    if not subscriptions:
        raise HTTPException(status_code=404, detail="No active push subscriptions found for your account")
        
    import json
    payload_data = json.dumps({
        "title": "Тестовое оповещение",
        "body": "Поздравляем! Пуш-уведомления успешно настроены.",
        "icon": "/favicon.ico",
        "url": "/admin/orders",
        "event_type": "test"
    }, ensure_ascii=False)

    # Сохраняем уведомление в историю БД
    new_notif = AdminNotification(
        user_id=current_user.id,
        title="Тестовое оповещение",
        body="Поздравляем! Пуш-уведомления успешно настроены.",
        url="/admin/orders",
        event_type="test",
        is_read=False
    )
    db.add(new_notif)
    db.commit()
    db.refresh(new_notif)
    
    success_count = 0
    removed_count = 0
    
    for sub in subscriptions:
        sub_info = {
            "endpoint": sub.endpoint,
            "keys": {
                "p256dh": sub.p256dh,
                "auth": sub.auth
            }
        }
        res = send_web_push(sub_info, payload_data, vapid_priv)
        if res == "success":
            success_count += 1
        elif res == "remove":
            db.delete(sub)
            removed_count += 1
            
    if removed_count > 0:
        db.commit()
        
    return {
        "success": True,
        "sent": success_count,
        "cleaned_expired": removed_count
    }

@router.get("", response_model=List[AdminNotification])
def get_admin_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Получить последние 40 уведомлений для текущего пользователя"""
    notifications = db.exec(
        select(AdminNotification)
        .where((AdminNotification.user_id == current_user.id) | (AdminNotification.user_id == None))
        .order_by(AdminNotification.created_at.desc())
        .limit(40)
    ).all()
    return notifications

@router.post("/{notification_id}/read")
def mark_notification_as_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Пометить уведомление как прочитанное"""
    notif = db.exec(select(AdminNotification).where(AdminNotification.id == notification_id)).first()
    if not notif:
        raise HTTPException(status_code=404, detail="Notification not found")
    
    if notif.user_id and notif.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to mark this notification as read")
        
    notif.is_read = True
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return {"success": True, "id": notif.id, "is_read": notif.is_read}

@router.post("/read-all")
def mark_all_notifications_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Пометить все уведомления пользователя как прочитанные"""
    unread_notifs = db.exec(
        select(AdminNotification)
        .where(((AdminNotification.user_id == current_user.id) | (AdminNotification.user_id == None)) & (AdminNotification.is_read == False))
    ).all()
    
    count = 0
    for notif in unread_notifs:
        notif.is_read = True
        db.add(notif)
        count += 1
        
    if count > 0:
        db.commit()
        
    return {"success": True, "marked_count": count}


@router.get("/feed")
def get_notifications_feed(
    category: str = "all",
    unread_only: bool = False,
    search: Optional[str] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Живая лента уведомлений в виде строк-плашек.
    Агрегирует события: новые заказы, смену статусов, оплаты Т-Банк, сообщения ВК и MAX.
    """
    from datetime import datetime, timezone
    from app.models.order import Order, OrderStatus

    items = []
    seen_keys = set()

    # 1. Загружаем сохраненные события из admin_notifications
    db_notifs = db.exec(
        select(AdminNotification)
        .where((AdminNotification.user_id == current_user.id) | (AdminNotification.user_id == None))
        .order_by(AdminNotification.created_at.desc())
        .limit(120)
    ).all()

    for n in db_notifs:
        key = n.external_key or f"db_{n.id}"
        seen_keys.add(key)
        cat = n.category or "system"
        if not n.category:
            if n.event_type == "new_order":
                cat = "new_order"
            elif n.event_type in ("new_payment", "tbank_payment"):
                cat = "tbank_payment"
            elif n.event_type in ("order_delivered", "order_cancelled", "order_changed", "delivery_assigned"):
                cat = "order_status"
            elif "vk" in n.event_type:
                cat = "vk_message"
            elif "max" in n.event_type:
                cat = "max_message"

        icon = "bx-bell"
        if cat == "new_order":
            icon = "bx-cart-add"
        elif cat == "order_status":
            icon = "bx-cycling" if "delivery" in (n.event_type or "") else "bx-transfer-alt"
        elif cat == "tbank_payment":
            icon = "bx-credit-card"
        elif cat == "vk_message":
            icon = "ri-vk-line"
        elif cat == "max_message":
            icon = "ri-chat-voice-line"

        target_url = n.url or "/orders"
        if target_url.startswith("/admin/"):
            target_url = target_url[6:]
        elif target_url == "/admin":
            target_url = "/orders"

        if cat == "tbank_payment" and ("/orders" in target_url or not target_url):
            target_url = "/bank/tbank-payments"
        elif cat in ("vk_message", "max_message"):
            target_url = "/multichat"
        elif n.order_id and ("/orders" in target_url) and ("order_id=" not in target_url):
            target_url = f"/orders?order_id={n.order_id}"

        if not target_url.startswith("/"):
            target_url = "/" + target_url

        items.append({
            "id": f"db_{n.id}",
            "db_id": n.id,
            "category": cat,
            "event_type": n.event_type,
            "title": n.title,
            "subtitle": n.subtitle or "",
            "body": n.body,
            "badge_text": n.badge_text or (
                "Новый заказ" if cat == "new_order" else
                "Статус заказа" if cat == "order_status" else
                "Оплата" if cat == "tbank_payment" else
                "ВКонтакте" if cat == "vk_message" else
                "MAX" if cat == "max_message" else "Система"
            ),
            "badge_color": n.badge_color or (
                "success" if cat in ("new_order", "max_message") else
                "warning" if cat == "order_status" else
                "info" if cat == "tbank_payment" else
                "primary" if cat == "vk_message" else "secondary"
            ),
            "icon": icon,
            "amount": n.amount,
            "order_id": n.order_id,
            "url": target_url,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() if hasattr(n.created_at, "isoformat") else str(n.created_at)
        })

    # 2. Агрегируем свежие заказы из таблицы orders (если еще нет в ленте)
    try:
        recent_orders = db.exec(
            select(Order)
            .order_by(Order.created_at.desc())
            .limit(30)
        ).all()
        for ord in recent_orders:
            ord_key = f"order_{ord.id}"
            if ord_key in seen_keys:
                continue
            seen_keys.add(ord_key)

            total_val = float(ord.total_with_discount if ord.total_with_discount is not None and ord.total_with_discount > 0 else ord.total_amount or 0.0)
            status_val = str(ord.status.value if hasattr(ord.status, "value") else ord.status).lower()
            status_ru = {
                "new": "Новый",
                "cooking": "Готовится",
                "ready": "Приготовлен",
                "delivering": "В пути (курьер)",
                "delivered": "Доставлен",
                "closed": "Завершен",
                "cancelled": "Отменен"
            }.get(status_val, status_val)

            is_status_event = status_val not in ("new", "draft")
            cat = "order_status" if is_status_event else "new_order"

            items.append({
                "id": ord_key,
                "db_id": None,
                "category": cat,
                "event_type": f"order_{status_val}",
                "title": f"Заказ №{ord.id}",
                "subtitle": f"{ord.order_type or 'Доставка'} • {status_ru} • {ord.courier_name or 'Курьер не назначен'}",
                "body": f"Клиент: {ord.customer_name or 'Гость'} ({ord.customer_phone or '-'}) • Адрес: {ord.delivery_address or 'Самовывоз'}",
                "badge_text": f"Статус: {status_ru}" if is_status_event else "Новый заказ",
                "badge_color": "warning" if is_status_event else "success",
                "icon": "bx-cycling" if is_status_event else "bx-cart-add",
                "amount": total_val,
                "order_id": ord.id,
                "url": f"/orders?order_id={ord.id}",
                "is_read": False,
                "created_at": ord.created_at.isoformat() if hasattr(ord.created_at, "isoformat") else str(ord.created_at)
            })
    except Exception as e:
        logger.warning(f"Error fetching orders for feed: {e}")

    # 3. Агрегируем проведенные оплаты Т-Банка из tbank_statements
    try:
        from app.models.tbank_settings import TBankAccountStatement
        statements = db.exec(
            select(TBankAccountStatement)
            .where(TBankAccountStatement.amount > 0)
            .order_by(TBankAccountStatement.charge_date.desc())
            .limit(20)
        ).all()
        for stmt in statements:
            stmt_key = f"tbank_stmt_{stmt.id}"
            if stmt_key in seen_keys:
                continue
            seen_keys.add(stmt_key)

            amt = float(stmt.amount or 0.0)
            items.append({
                "id": stmt_key,
                "db_id": None,
                "category": "tbank_payment",
                "event_type": "tbank_payment",
                "title": f"Оплата Т-Банк: +{amt:,.0f} ₽".replace(",", " "),
                "subtitle": f"Плательщик: {stmt.payer_name or 'Физическое лицо'} • Р/С: {stmt.account_number or '-'}",
                "body": stmt.payment_purpose or "Пополнение счета / Оплата заказа",
                "badge_text": "Т-Банк Выписка",
                "badge_color": "info",
                "icon": "bx-credit-card",
                "amount": amt,
                "order_id": stmt.matched_order_id,
                "url": f"/bank/tbank-payments",
                "is_read": False,
                "created_at": stmt.charge_date.isoformat() if hasattr(stmt.charge_date, "isoformat") else str(stmt.charge_date)
            })
    except Exception as e:
        logger.warning(f"Error fetching tbank statements for feed: {e}")

    # 4. Агрегируем входящие сообщения Мультичата (ВК и MAX)
    try:
        from app.models.chat import MultichatMessage
        chat_msgs = db.exec(
            select(MultichatMessage)
            .where(MultichatMessage.direction.in_(["inbound", "in"]))
            .order_by(MultichatMessage.created_at.desc())
            .limit(30)
        ).all()
        for m in chat_msgs:
            m_key = f"chat_{m.id}"
            if m_key in seen_keys:
                continue
            seen_keys.add(m_key)

            ch = (m.channel or "").lower()
            is_vk = "vk" in ch
            is_max = "max" in ch

            cat = "vk_message" if is_vk else ("max_message" if is_max else "system")
            if cat not in ("vk_message", "max_message"):
                continue

            badge_text = "ВКонтакте" if is_vk else "MAX"
            if "user" in ch or "account" in ch or "bridge" in ch:
                badge_text += " (Личный №)"
            else:
                badge_text += " (Бот/Группа)"

            items.append({
                "id": m_key,
                "db_id": None,
                "category": cat,
                "event_type": f"{cat}_incoming",
                "title": f"Сообщение от {m.peer_name or m.peer_id or 'Клиент'}",
                "subtitle": f"Канал: {badge_text} • ID: {m.peer_id or '-'}",
                "body": m.text or "[Вложение / Медиа]",
                "badge_text": badge_text,
                "badge_color": "primary" if is_vk else "success",
                "icon": "ri-vk-line" if is_vk else "ri-chat-voice-line",
                "amount": None,
                "order_id": None,
                "url": "/multichat",
                "is_read": getattr(m, "is_read", False),
                "created_at": m.created_at.isoformat() if hasattr(m.created_at, "isoformat") else str(m.created_at)
            })
    except Exception as e:
        logger.warning(f"Error fetching chat messages for feed: {e}")

    # Сортировка по дате (свежие сверху)
    items.sort(key=lambda x: str(x.get("created_at") or ""), reverse=True)

    # Подсчет счетчиков по категориям (до фильтрации)
    counts = {
        "all": len(items),
        "unread": sum(1 for x in items if not x.get("is_read")),
        "new_order": sum(1 for x in items if x.get("category") == "new_order"),
        "order_status": sum(1 for x in items if x.get("category") == "order_status"),
        "tbank_payment": sum(1 for x in items if x.get("category") == "tbank_payment"),
        "vk_message": sum(1 for x in items if x.get("category") == "vk_message"),
        "max_message": sum(1 for x in items if x.get("category") == "max_message")
    }

    # Применение фильтров
    filtered = items
    if category and category != "all":
        filtered = [x for x in filtered if x.get("category") == category]

    if unread_only:
        filtered = [x for x in filtered if not x.get("is_read")]

    if search and search.strip():
        s = search.strip().lower()
        filtered = [
            x for x in filtered
            if s in (x.get("title") or "").lower()
            or s in (x.get("body") or "").lower()
            or s in (x.get("subtitle") or "").lower()
            or s in str(x.get("order_id") or "")
            or s in str(x.get("amount") or "")
        ]

    return {
        "counts": counts,
        "items": filtered[:limit]
    }
