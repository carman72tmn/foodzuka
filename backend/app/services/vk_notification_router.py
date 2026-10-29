import logging
from typing import Optional, Dict, Any, List
from sqlmodel import Session, select
from app.core.database import engine
import re
from datetime import datetime, timedelta
from app.models.vk_bot import VkBotAccount, VkBotSubscription, VkBotMessageLog, DeliveryMode, MessageStatus, VkTemplate, CourierOrderNotification
from app.services.vk_bot_service import vk_bot_service

logger = logging.getLogger(__name__)

def get_telegram_token(session: Session) -> Optional[str]:
    from app.models.bot_settings import BotSettings
    import os
    bot_settings = session.exec(select(BotSettings)).first()
    if bot_settings:
        if not getattr(bot_settings, "is_bot_active", True) or not getattr(bot_settings, "is_system_notifications_active", True):
            return None
        return bot_settings.telegram_bot_token or os.getenv("TELEGRAM_BOT_TOKEN")
    return os.getenv("TELEGRAM_BOT_TOKEN")

async def send_telegram_message(chat_id: int, text: str, token: str, reply_markup: Optional[dict] = None) -> Dict[str, Any]:
    import httpx
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "HTML"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(url, json=payload)
            res_json = response.json() if response.status_code in [200, 201] else {}
            mid = res_json.get("result", {}).get("message_id")
            return {"success": response.status_code in [200, 201] and res_json.get("ok"), "message_id": str(mid or "")}
    except Exception as e:
        logger.error(f"Failed to send Telegram message to {chat_id}: {e}")
        return {"success": False, "error": str(e)}

async def send_max_message_helper(
    target: str, 
    text: str, 
    session: Session,
    bot_id: Optional[int] = None,
    prefer_channel: Optional[str] = None,
    image_path: Optional[str] = None,
    image_url: Optional[str] = None,
    buttons: Optional[List[List[Dict[str, Any]]]] = None
) -> Dict[str, Any]:
    from app.services.max_service import send_max_message
    res = await send_max_message(
        recipient=target, 
        text=text, 
        session=session,
        bot_id=bot_id,
        prefer_channel=prefer_channel,
        image_path=image_path,
        image_url=image_url,
        buttons=buttons
    )
    return {"success": bool(res), "msg_id": res.get("msg_id"), "error": res.get("error")}

async def send_telegram_photo(chat_id: int, photo_path: str, caption: str, token: str, reply_markup: Optional[dict] = None) -> Dict[str, Any]:
    import httpx
    import json
    url = f"https://api.telegram.org/bot{token}/sendPhoto"
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            safe_caption = caption[:1020] + "..." if (caption and len(caption) > 1024) else caption
            with open(photo_path, "rb") as f:
                files = {"photo": f}
                data = {
                    "chat_id": chat_id,
                    "caption": safe_caption,
                    "parse_mode": "HTML"
                }
                if reply_markup:
                    data["reply_markup"] = json.dumps(reply_markup)
                response = await client.post(url, data=data, files=files)
                res_json = response.json() if response.status_code in [200, 201] else {}
                mid = res_json.get("result", {}).get("message_id")
                return {"success": response.status_code in [200, 201] and res_json.get("ok"), "message_id": str(mid or "")}
    except Exception as e:
        logger.error(f"Failed to send Telegram photo to {chat_id}: {e}")
        return {"success": False, "error": str(e)}

def build_order_status_header(order: Any, event_type: str = "") -> str:
    if not order:
        return "📦 ЗАКАЗ"
    order_num = getattr(order, 'iiko_order_number', None) or getattr(order, 'external_number', None) or getattr(order, 'external_id', None) or getattr(order, 'id', '')
    status = str(getattr(order, 'status', '')).lower()
    if status in ("delivered", "closed", "доставлен", "закрыт"):
        return f"✅ ЗАКАЗ #{order_num} ДОСТАВЛЕН"
    if status in ("new", "cookingstarted", "waitcooking", "cooking", "готовится", "новый", "ждет готовки", "ждет готовности"):
        from app.core.datetime_utils import to_local, get_local_now
        ready_time_str = ""
        mins_left = None
        exp_dt = getattr(order, 'expected_ready_time', None) or getattr(order, 'complete_before', None) or getattr(order, 'cooking_finish_time', None)
        if exp_dt:
            if isinstance(exp_dt, str):
                try:
                    exp_dt = datetime.fromisoformat(exp_dt.replace("Z", "+00:00"))
                except Exception:
                    try:
                        exp_dt = datetime.strptime(exp_dt, "%Y-%m-%d %H:%M:%S")
                    except Exception:
                        exp_dt = None
            if isinstance(exp_dt, datetime):
                try:
                    loc_dt = to_local(exp_dt, "Asia/Yekaterinburg")
                    ready_time_str = loc_dt.strftime("%H:%M")
                    diff = (loc_dt - get_local_now("Asia/Yekaterinburg")).total_seconds() / 60
                    if diff > 0:
                        mins_left = int(diff)
                except Exception:
                    pass
        if ready_time_str and mins_left is not None:
            return f"⏳ ОЖИДАЕТ ГОТОВНОСТИ • Готов к {ready_time_str} (через ~{mins_left} мин)"
        elif ready_time_str:
            return f"⏳ ОЖИДАЕТ ГОТОВНОСТИ • Готов к {ready_time_str}"
        else:
            return f"⏳ ОЖИДАЕТ ГОТОВНОСТИ НА КУХНЕ"
    if status in ("cookingcompleted", "waiting", "ready", "ready_for_pickup", "готов", "готов к выдаче"):
        return f"🚀 ЗАКАЗ #{order_num} ГОТОВ К ВЫДАЧЕ"
    if status in ("onway", "delivering", "в пути", "у курьера"):
        return f"🚀 АКТИВНЫЙ ЗАКАЗ #{order_num} • В ПУТИ"
    return f"📦 ЗАКАЗ #{order_num}"

def build_courier_nav_data(order: Any) -> Dict[str, str]:
    """
    Формирует полный адрес для курьера и ссылки для навигаторов (Яндекс.Навигатор и 2ГИС).
    Гарантирует, что при клике на ссылку в навигаторе открывается полный адрес с домом, подъездом, этажом и квартирой.
    """
    import urllib.parse
    
    def _p(name):
        if isinstance(order, dict):
            return order.get(name)
        return getattr(order, name, None)
        
    addr = str(_p("delivery_address") or _p("address") or "").strip()
    city = str(_p("city") or "Тюмень").strip()
    street = _p("street")
    house = _p("house")
    entrance = _p("entrance")
    floor = _p("floor")
    flat = _p("flat")
    doorphone = _p("doorphone")
    
    if not addr or addr in ("---", "Самовывоз"):
        parts = [p for p in (city, street, f"д. {house}" if house and str(house) != "0" else None) if p]
        addr = ", ".join(parts)
        
    extras = []
    addr_lower = addr.lower()
    if entrance and str(entrance).strip() and "под" not in addr_lower:
        extras.append(f"под. {entrance}")
    if floor and str(floor).strip() and "эт" not in addr_lower:
        extras.append(f"эт. {floor}")
    if flat and str(flat).strip() and "кв" not in addr_lower:
        extras.append(f"кв. {flat}")
    if doorphone and str(doorphone).strip() and "домофон" not in addr_lower:
        extras.append(f"домофон {doorphone}")
        
    full_address = f"{addr}, {', '.join(extras)}" if extras and addr else (addr or "---")
    
    if full_address and full_address not in ("---", "Самовывоз"):
        encoded_full = urllib.parse.quote_plus(full_address)
        yandex_url = f"https://yandex.ru/maps/?rtext=~{encoded_full}&rtt=auto"
        dgis_url = f"https://2gis.ru/search/{encoded_full}"
    else:
        yandex_url = ""
        dgis_url = ""
        
    return {
        "full_address": full_address,
        "map_yandex": yandex_url,
        "map_2gis": dgis_url
    }

def build_courier_action_keyboards(order: Any) -> Dict[str, Any]:
    import json
    order_id = getattr(order, 'id', None)
    is_paid = bool(getattr(order, 'is_paid', False))
    nav_data = build_courier_nav_data(order)
    nav_url = nav_data["map_yandex"]
        
    vk_buttons = []
    if nav_url:
        vk_buttons.append([{"action": {"type": "open_link", "link": nav_url, "label": "🧭 Яндекс.Навигатор"}}])
    if is_paid:
        vk_buttons.append([{"action": {"type": "callback", "label": "✅ Заказ доставлен", "payload": json.dumps({"cmd": "courier_deliver", "order_id": order_id, "pay": "paid"}, ensure_ascii=False)}, "color": "positive"}])
    else:
        vk_buttons.append([
            {"action": {"type": "callback", "label": "📱 Доставлен (СБП QR)", "payload": json.dumps({"cmd": "courier_deliver", "order_id": order_id, "pay": "sbp"}, ensure_ascii=False)}, "color": "positive"},
            {"action": {"type": "callback", "label": "💵 Наличные", "payload": json.dumps({"cmd": "courier_deliver", "order_id": order_id, "pay": "cash"}, ensure_ascii=False)}, "color": "primary"}
        ])
        vk_buttons.append([
            {"action": {"type": "callback", "label": "💳 Терминал (Картой)", "payload": json.dumps({"cmd": "courier_deliver", "order_id": order_id, "pay": "card"}, ensure_ascii=False)}, "color": "secondary"}
        ])
    vk_keyboard = {"inline": True, "buttons": vk_buttons}
    
    tg_buttons = []
    if nav_url:
        tg_buttons.append([{"text": "🧭 Яндекс.Навигатор", "url": nav_url}])
    if is_paid:
        tg_buttons.append([{"text": "✅ Заказ доставлен", "callback_data": f"cdeliv:{order_id}:paid"}])
    else:
        tg_buttons.append([
            {"text": "📱 Доставлен (СБП QR)", "callback_data": f"cdeliv:{order_id}:sbp"},
            {"text": "💵 Наличные", "callback_data": f"cdeliv:{order_id}:cash"}
        ])
        tg_buttons.append([{"text": "💳 Терминал (Картой)", "callback_data": f"cdeliv:{order_id}:card"}])
    tg_keyboard = {"inline_keyboard": tg_buttons}
    
    max_buttons = []
    if nav_url:
        max_buttons.append([{"type": "link", "text": "🧭 Яндекс.Навигатор", "url": nav_url}])
    if is_paid:
        max_buttons.append([{"type": "callback", "text": "✅ Заказ доставлен", "payload": f"cdeliv:{order_id}:paid"}])
    else:
        max_buttons.append([
            {"type": "callback", "text": "📱 Доставлен (СБП QR)", "payload": f"cdeliv:{order_id}:sbp"},
            {"type": "callback", "text": "💵 Наличные", "payload": f"cdeliv:{order_id}:cash"}
        ])
        max_buttons.append([{"type": "callback", "text": "💳 Терминал (Картой)", "payload": f"cdeliv:{order_id}:card"}])
        
    return {"vk": vk_keyboard, "tg": tg_keyboard, "telegram": tg_keyboard, "max": max_buttons, "nav_url": nav_url}

def build_collapsed_delivered_text(order: Any, payment_label: str = "") -> str:
    import urllib.parse
    from app.core.datetime_utils import get_local_now
    order_num = getattr(order, 'iiko_order_number', None) or getattr(order, 'external_number', None) or getattr(order, 'id', '')
    total = getattr(order, 'total_amount', 0) or 0
    pay_str = payment_label or getattr(order, 'payment_method_name', None) or ("Оплачено" if getattr(order, 'is_paid', False) else "При получении")
    nav_data = build_courier_nav_data(order)
    addr = nav_data["full_address"]
    yandex_url = nav_data["map_yandex"]
    dgis_url = nav_data["map_2gis"]
    if yandex_url and dgis_url:
        nav_links = f"\n📍 Адрес: {addr}\n🧭 Яндекс.Навигатор: {yandex_url}\n🗺 2ГИС: {dgis_url}"
    else:
        nav_links = f"\n📍 Адрес: {addr}"
    now_hm = get_local_now("Asia/Yekaterinburg").strftime("%H:%M")
    return (
        f"✅ ЗАКАЗ №{order_num} ДОСТАВЛЕН ({now_hm})\n"
        f"💰 Сумма: {int(float(total))} ₽ • Оплата: {pay_str}\n"
        f"📞 Клиент: {phone}"
        f"{nav_links}"
    )

async def edit_telegram_courier_message(
    tg_token: str, 
    chat_id: str, 
    message_id: str, 
    new_text: str, 
    reply_markup: Optional[Dict] = None, 
    remove_photo: bool = False
) -> Dict[str, Any]:
    import httpx
    if remove_photo:
        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                await client.post(
                    f"https://api.telegram.org/bot{tg_token}/deleteMessage",
                    json={"chat_id": int(chat_id), "message_id": int(message_id)}
                )
        except Exception:
            pass
        send_url = f"https://api.telegram.org/bot{tg_token}/sendMessage"
        payload = {"chat_id": int(chat_id), "text": new_text, "parse_mode": "HTML"}
        if reply_markup:
            payload["reply_markup"] = reply_markup
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(send_url, json=payload)
                res_data = resp.json()
                new_mid = res_data.get("result", {}).get("message_id")
                return {"success": resp.status_code in [200, 201], "message_id": str(new_mid or message_id)}
        except Exception as e:
            return {"success": False, "error": str(e)}
    else:
        caption_url = f"https://api.telegram.org/bot{tg_token}/editMessageCaption"
        caption_payload = {"chat_id": int(chat_id), "message_id": int(message_id), "caption": new_text[:1020], "parse_mode": "HTML"}
        if reply_markup:
            caption_payload["reply_markup"] = reply_markup
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(caption_url, json=caption_payload)
                if resp.status_code in [200, 201]:
                    return {"success": True, "message_id": message_id}
                text_url = f"https://api.telegram.org/bot{tg_token}/editMessageText"
                text_payload = {"chat_id": int(chat_id), "message_id": int(message_id), "text": new_text, "parse_mode": "HTML"}
                if reply_markup:
                    text_payload["reply_markup"] = reply_markup
                resp2 = await client.post(text_url, json=text_payload)
                return {"success": resp2.status_code in [200, 201], "message_id": message_id}
        except Exception as e:
            return {"success": False, "error": str(e)}

async def collapse_order_notifications_on_delivery(
    order_id: int, 
    payment_label: str = "", 
    session: Optional[Session] = None
) -> None:
    from app.core.database import engine
    from app.models.order import Order
    from app.models.vk_bot import CourierOrderNotification
    from app.services.vk_bot_service import vk_bot_service
    from app.services.max_service import edit_max_message
    from app.core.datetime_utils import utc_now
    
    s = session
    need_close = False
    if not s:
        s = Session(engine)
        need_close = True
    try:
        notifs = s.exec(
            select(CourierOrderNotification)
            .where(CourierOrderNotification.order_id == order_id)
            .where(CourierOrderNotification.is_collapsed == False)
            .where(CourierOrderNotification.external_message_id != None)
        ).all()
        if not notifs:
            return
        order = s.get(Order, order_id)
        if not order:
            return
        compact_text = build_collapsed_delivered_text(order, payment_label)
        from app.models.validation_settings import ValidationSettings
        val_settings = s.exec(select(ValidationSettings)).first()
        tg_token = val_settings.telegram_bot_token if val_settings else None
        
        for notif in notifs:
            try:
                if notif.channel == "vk" and notif.external_chat_id and notif.external_message_id:
                    await vk_bot_service.edit_message(
                        peer_id=int(notif.external_chat_id),
                        message_id=int(notif.external_message_id),
                        message=compact_text,
                        attachment="",
                        keyboard={"buttons": [], "inline": True}
                    )
                elif notif.channel == "tg" and notif.external_chat_id and notif.external_message_id and tg_token:
                    await edit_telegram_courier_message(
                        tg_token=tg_token,
                        chat_id=notif.external_chat_id,
                        message_id=notif.external_message_id,
                        new_text=compact_text,
                        reply_markup={"inline_keyboard": []},
                        remove_photo=True
                    )
                elif notif.channel == "max" and notif.external_chat_id and notif.external_message_id:
                    await edit_max_message(
                        message_id=notif.external_message_id,
                        recipient=notif.external_chat_id,
                        text=compact_text,
                        buttons=[],
                        keep_image=False,
                        session=s,
                        bot_id=notif.bot_id
                    )
            except Exception as e_edit:
                logger.warning(f"Error collapsing notification #{notif.id} ({notif.channel}): {e_edit}")
            notif.status = "delivered"
            notif.is_collapsed = True
            notif.delivered_at = utc_now()
            if payment_label:
                notif.payment_method_selected = payment_label
            s.add(notif)
        s.commit()
    finally:
        if need_close:
            s.close()

async def handle_courier_order_action(
    order_id: int, 
    payment_code: str, 
    channel: str, 
    actor_identifier: str
) -> Dict[str, Any]:
    from app.core.database import engine
    from app.models.order import Order
    from app.models.admin_notification import AdminNotification
    from app.core.datetime_utils import utc_now
    payment_labels = {
        "sbp": "СБП (QR-код)",
        "cash": "Наличные",
        "card": "Терминал (Картой курьеру)",
        "paid": "Онлайн / Оплачено"
    }
    pay_label = payment_labels.get(str(payment_code).lower(), payment_code)
    with Session(engine) as db:
        order = db.get(Order, order_id)
        if not order:
            return {"success": False, "error": f"Заказ #{order_id} не найден"}
        order_num = getattr(order, 'iiko_order_number', None) or getattr(order, 'external_number', None) or getattr(order, 'id', '')
        order.status = "Delivered"
        order.is_paid = True
        if hasattr(order, 'actual_delivery_time'):
            order.actual_delivery_time = utc_now()
        if hasattr(order, 'courier_notification_status'):
            order.courier_notification_status = "delivered"
        if hasattr(order, 'payment_method_name'):
            order.payment_method_name = pay_label
        db.add(order)
        notif = AdminNotification(
            notification_type="status",
            title=f"✅ Курьер доставил заказ #{order_num}",
            message=f"Заказ #{order_num} отмечен как доставленный через {channel.upper()}.\nСпособ оплаты: {pay_label}.",
            order_id=order.id,
            status="delivered",
            url=f"/admin/orders?order_id={order.id}"
        )
        db.add(notif)
        db.commit()

        # Синхронизация статуса доставки с iiko Cloud при закрытии курьером
        iiko_oid = getattr(order, 'iiko_order_id', None)
        if iiko_oid:
            try:
                from app.services.iiko_service import iiko_service
                from app.models.iiko_settings import IikoSettings
                iiko_cfg = db.exec(select(IikoSettings)).first()
                if iiko_cfg and iiko_cfg.organization_id:
                    await iiko_service.change_delivery_status(
                        organization_id=str(iiko_cfg.organization_id),
                        order_id=str(iiko_oid),
                        delivery_status="Delivered"
                    )
            except Exception as e_iiko:
                logger.warning(f"Could not update status in iiko for order #{order_num}: {e_iiko}")

        await collapse_order_notifications_on_delivery(order.id, payment_label=pay_label, session=db)
        return {"success": True, "order_id": order.id, "payment": pay_label}

def _load_qr_font(size: int, bold: bool = True):
    from PIL import ImageFont
    import os
    candidates = [
        "/app/media/fonts/Roboto-Bold.ttf" if bold else "/app/media/fonts/Roboto-Regular.ttf",
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app", "media", "fonts", "Roboto-Bold.ttf")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "media", "fonts", "Roboto-Bold.ttf")),
        "c:/Users/v_kva/.gemini/antigravity/scratch/foodtech/backend/app/media/fonts/Roboto-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf",
        "C:/Windows/Fonts/arial.ttf"
    ]
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                pass
    return ImageFont.load_default()

def _wrap_qr_text(text: str, font, max_width: int, draw) -> List[str]:
    if not text:
        return []
    words = str(text).split()
    lines = []
    current_line = []
    for word in words:
        test_line = " ".join(current_line + [word])
        bbox = draw.textbbox((0, 0), test_line, font=font)
        w = bbox[2] - bbox[0]
        if w <= max_width:
            current_line.append(word)
        else:
            if current_line:
                lines.append(" ".join(current_line))
                current_line = [word]
            else:
                lines.append(word)
    if current_line:
        lines.append(" ".join(current_line))
    return lines

async def generate_sbp_qr_image(
    order_id: int, 
    amount: float, 
    session: Session,
    order_number: Optional[str] = None,
    delivery_address: Optional[str] = None
) -> Optional[str]:
    """
    Генерирует фирменную PNG-картинку QR-кода СБП для оплаты заказа.
    Наносит информационную плашку с номером заказа, суммой к оплате и адресом доставки.
    Возвращает локальный путь к сохраненному файлу на сервере или None при ошибке.
    """
    import qrcode
    from PIL import Image, ImageDraw
    import io
    import os
    import time
    import httpx
    from datetime import datetime
    from app.models.tbank_settings import TBankSettings
    from app.core.tbank_utils import generate_tbank_qrpay_signature
    from app.models.order import Order
    
    settings = session.exec(select(TBankSettings)).first()
    
    # Если номер или адрес не переданы, получаем из БД
    if not order_number or not delivery_address:
        db_order = session.get(Order, order_id)
        if db_order:
            if not order_number:
                order_number = str(db_order.external_number or db_order.id)
            if not delivery_address:
                delivery_address = str(db_order.delivery_address or "---")
                
    order_number = str(order_number or order_id)
    delivery_address = str(delivery_address or "Адрес не указан")
    
    # Путь для сохранения картинки в примапленной папке медиа
    qr_dir = "/app/media/img/qr"
    if not os.path.exists("/app"):
        # Локальный фолбэк для тестов
        qr_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "backend", "app", "media", "img", "qr"))
    os.makedirs(qr_dir, exist_ok=True)
    file_path = f"{qr_dir}/order_{order_id}_{int(time.time())}.png"
    
    code_url = None
    
    if not settings or not settings.is_active:
        logger.info(f"T-Bank API is not active. Using demo SBP link for order {order_id}")
        code_url = f"https://qr.nspk.ru/AD1000787B2943B2943B2943B2943B29?orderId={order_id}&amount={amount}"
    else:
        from app.core.tbank_utils import get_tbank_sbp_credentials
        mch_id, ter_id, secret_key = get_tbank_sbp_credentials(settings)
        try:
            url = "https://qrpay.tinkoff.ru/qrpay/external/api/v1/operations/QRPAY"
            out_transaction_no = str(int(time.time() * 100))
            amount_str = f"{amount:.2f}"
            
            payload = {
                "mchId": mch_id,
                "terId": ter_id,
                "currency": "643",
                "totalAmount": amount_str,
                "outTransactionNo": out_transaction_no,
                "subject": f"Оплата заказа №{order_id} в FoodZuka",
                "tradeType": "pay.paxpay.native",
                "version": "V1.0",
                "signType": "HMAC_SHA256",
                "timeStart": datetime.now().strftime("%Y-%m-%dT%H:%M:%S")
            }
            
            payload["signature"] = generate_tbank_qrpay_signature(payload, secret_key, "qrpay")
            
            async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
                res = await client.post(url, json=payload)
                if res.status_code == 200:
                    res_data = res.json()
                    if res_data.get("code") == "SUCCESS":
                        code_url = res_data.get("codeUrl")
                        logger.info(f"Successfully generated real T-Bank SBP URL for order {order_id} (terId={ter_id})")
                    else:
                        logger.warning(f"T-Bank API rejected QRPAY: {res_data}")
                else:
                    logger.warning(f"T-Bank API HTTP error ({res.status_code}): {res.text}")
        except Exception as e:
            logger.error(f"Error calling T-Bank QRPAY API: {e}")
            
        if not code_url:
            code_url = f"https://qr.nspk.ru/AD1000787B2943B2943B2943B2943B29?orderId={order_id}&amount={amount}"

    try:
        # 1. Генерация базового QR-кода
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(code_url)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF").convert("RGBA")
        qr_size = 320
        qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)
        
        # 2. Шрифты и размеры холста
        card_width = 480
        f_badge = _load_qr_font(12, bold=True)
        f_title = _load_qr_font(22, bold=True)
        f_amount_lbl = _load_qr_font(12, bold=False)
        f_amount_val = _load_qr_font(24, bold=True)
        f_addr_lbl = _load_qr_font(12, bold=False)
        f_addr_val = _load_qr_font(15, bold=True)
        
        # Перенос строк адреса
        temp_img = Image.new("RGBA", (card_width, 100), (255, 255, 255, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        addr_lines = _wrap_qr_text(delivery_address, f_addr_val, card_width - 56, temp_draw)
        
        line_h = 20
        addr_block_h = max(38, len(addr_lines) * line_h + 24)
        
        header_h = 80
        amount_h = 58
        total_h = header_h + qr_size + 16 + amount_h + 12 + addr_block_h + 20
        
        # 3. Отрисовка карточки
        canvas = Image.new("RGBA", (card_width, total_h), (248, 250, 252, 255))
        draw = ImageDraw.Draw(canvas)
        
        # Внешняя рамка
        draw.rounded_rectangle([4, 4, card_width - 5, total_h - 5], radius=16, fill="#FFFFFF", outline="#E2E8F0", width=2)
        
        # Шапка карточки: бейдж СБП
        draw.rounded_rectangle([16, 16, 160, 38], radius=6, fill="#0284C7")
        draw.text((26, 21), "СБП • ОПЛАТА", fill="#FFFFFF", font=f_badge)
        
        # Номер заказа
        title_text = f"Заказ № {order_number}"
        draw.text((16, 44), title_text, fill="#0F172A", font=f_title)
        
        # Позиционирование QR-кода
        qr_x = (card_width - qr_size) // 2
        qr_y = header_h + 8
        draw.rounded_rectangle([qr_x - 6, qr_y - 6, qr_x + qr_size + 6, qr_y + qr_size + 6], radius=12, fill="#FFFFFF", outline="#E2E8F0", width=1)
        canvas.paste(qr_img, (qr_x, qr_y), qr_img)
        
        # Блок суммы к оплате
        amt_y = qr_y + qr_size + 16
        draw.rounded_rectangle([16, amt_y, card_width - 16, amt_y + amount_h], radius=10, fill="#F0FDF4", outline="#BBF7D0", width=1)
        draw.text((28, amt_y + 8), "СУММА К ОПЛАТЕ:", fill="#166534", font=f_amount_lbl)
        formatted_amount = f"{amount:,.0f} ₽".replace(",", " ")
        draw.text((28, amt_y + 24), formatted_amount, fill="#15803D", font=f_amount_val)
        
        # Блок адреса доставки
        addr_y = amt_y + amount_h + 10
        draw.rounded_rectangle([16, addr_y, card_width - 16, addr_y + addr_block_h], radius=10, fill="#F8FAFC", outline="#E2E8F0", width=1)
        draw.text((26, addr_y + 6), "АДРЕС ДОСТАВКИ:", fill="#64748B", font=f_addr_lbl)
        
        curr_y = addr_y + 22
        for line in addr_lines:
            draw.text((26, curr_y), line, fill="#1E293B", font=f_addr_val)
            curr_y += line_h
            
        canvas.convert("RGB").save(file_path, "PNG", quality=95)
        logger.info(f"Saved annotated SBP QR code image for order {order_id} (No. {order_number}, Sum {amount}) to {file_path}")
        return file_path
    except Exception as e:
        logger.error(f"Failed to generate annotated QR image: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None


class VkNotificationRouter:
    def render_template(self, template_text: str, context: dict) -> str:
        """
        Рендерит шаблон, заменяя {{key.subkey}} на значения из context.
        Поддерживает синонимы:
        - customer.categories -> iiko_categories
        - order.address -> delivery_address
        - customer.bonus_points -> bonus_points
        - customer.notes -> notes
        """
        if not template_text:
            return ""
            
        def replace_var(match):
            var_path = match.group(1).strip()
            
            # Обработка customer.*
            if var_path.startswith("customer."):
                customer = context.get("customer")
                order = context.get("order") or {}
                
                # Извлекаем customer_info_details из заказа, если он есть
                cust_details = {}
                if isinstance(order, dict):
                    cust_details = order.get("customer_info_details") or {}
                else:
                    cust_details = getattr(order, "customer_info_details", {}) or {}
                if not isinstance(cust_details, dict):
                    cust_details = {}
                    
                field = var_path.split(".", 1)[1].strip()
                
                # 1. Сначала пробуем получить из customer_info_details (карточки заказа)
                val = None
                if field == "phone":
                    val = cust_details.get("phone") or cust_details.get("customer_phone")
                    if not val:
                        # Фолбэк на телефон из самого заказа
                        if isinstance(order, dict):
                            val = order.get("customer_phone")
                        else:
                            val = getattr(order, "customer_phone", None)
                elif field == "bonus_points":
                    val = cust_details.get("bonus_points") or cust_details.get("bonus_balance")
                elif field == "categories":
                    val = cust_details.get("categories") or cust_details.get("iiko_categories")
                elif field == "notes":
                    val = cust_details.get("notes") or cust_details.get("iiko_notes")
                elif field == "name":
                    val = cust_details.get("name") or cust_details.get("customer_name")
                    if not val:
                        if isinstance(order, dict):
                            val = order.get("customer_name")
                        else:
                            val = getattr(order, "customer_name", None)
                
                # 2. Если в карточке заказа (снимок) не найдено, пробуем взять из связанного customer
                if val is None and customer:
                    actual_field = field
                    if field == "categories":
                        actual_field = "iiko_categories"
                    elif field == "bonus_points":
                        actual_field = "bonus_points"
                        
                    if isinstance(customer, dict):
                        val = customer.get(actual_field)
                    elif hasattr(customer, actual_field):
                        val = getattr(customer, actual_field)
                        
                # Форматирование значения
                if field == "categories":
                    if isinstance(val, list):
                        return ", ".join(str(x) for x in val) if val else "---"
                    return str(val) if val else "---"
                
                if val is None or val == "":
                    # Фолбэки по умолчанию
                    if field == "phone": return "---"
                    if field == "bonus_points": return "0"
                    if field == "name": return "Гость"
                    return "---"
                    
                return str(val)
                
            # Обработка order.*
            elif var_path.startswith("order."):
                order = context.get("order")
                if not order:
                    return ""
                field = var_path.split(".", 1)[1].strip()
                
                # Вспомогательная функция для безопасного извлечения атрибутов/ключей
                def _get_ord_prop(prop_name):
                    if isinstance(order, dict):
                        return order.get(prop_name)
                    return getattr(order, prop_name, None)

                val = None
                # 1. Адрес, номер, состав
                if field in ("address", "delivery_address"):
                    nav_d = build_courier_nav_data(order)
                    val = nav_d["full_address"] or _get_ord_prop("delivery_address") or _get_ord_prop("address")
                elif field in ("number", "external_number", "order_number"):
                    val = _get_ord_prop("external_number") or _get_ord_prop("order_number") or _get_ord_prop("number")
                elif field in ("items", "items_text", "items_summary"):
                    val = _get_ord_prop("items_text") or _get_ord_prop("items_summary") or _get_ord_prop("items")

                # 2. Ссылки на карты и навигаторы (Строго по полному адресу с подъездом и квартирой)
                elif field in ("map_yandex", "yandex_maps"):
                    val = _get_ord_prop("map_yandex") or _get_ord_prop("yandex_maps")
                    if not val or str(val).strip() in ("", "---") or "pt=" in str(val) or "%2C+0" in str(val):
                        nav_d = build_courier_nav_data(order)
                        val = nav_d["map_yandex"]

                elif field in ("map_2gis", "2gis", "two_gis"):
                    val = _get_ord_prop("map_2gis") or _get_ord_prop("2gis")
                    if not val or str(val).strip() in ("", "---") or "/geo/" in str(val) or "%2C+0" in str(val):
                        nav_d = build_courier_nav_data(order)
                        val = nav_d["map_2gis"]

                elif field in ("yandex_navigator", "map_navigator", "navigator", "map_navi"):
                    val = _get_ord_prop("yandex_navigator") or _get_ord_prop("map_navigator")
                    if not val or str(val).strip() in ("", "---") or "pt=" in str(val) or "%2C+0" in str(val):
                        nav_d = build_courier_nav_data(order)
                        val = nav_d["map_yandex"]

                # 3. Время прибытия и приготовления
                elif field in ("pickup_time", "arrival_time", "ready_time"):
                    val = _get_ord_prop("pickup_time") or _get_ord_prop("arrival_time") or _get_ord_prop("ready_time")
                    if not val or str(val).strip() in ("", "---", "None"):
                        from app.core.datetime_utils import utc_now, to_local
                        c_mins = 0
                        try:
                            c_mins = int(_get_ord_prop("cooking_time_minutes") or 0)
                        except:
                            c_mins = 0
                        if c_mins > 0:
                            updated_at = _get_ord_prop("cooking_time_updated_at")
                            base_dt = updated_at if isinstance(updated_at, datetime) else utc_now()
                            try:
                                ready_dt = to_local(base_dt, "Asia/Yekaterinburg") + timedelta(minutes=c_mins)
                            except Exception:
                                ready_dt = base_dt + timedelta(minutes=c_mins)
                            val = ready_dt.strftime("%H:%M")
                        else:
                            exp = _get_ord_prop("expected_time")
                            if exp:
                                val = exp.strftime("%H:%M") if isinstance(exp, datetime) else str(exp)
                            else:
                                val = "Уточняется на кухне"

                elif field in ("cooking_time", "cooking_time_minutes"):
                    val = _get_ord_prop("cooking_time_minutes") or _get_ord_prop("cooking_time")
                    if field == "cooking_time":
                        try:
                            c_int = int(val or 0)
                            val = f"{c_int} мин." if c_int > 0 else "Не задано"
                        except:
                            val = str(val) if val else "Не задано"

                elif field in ("delivery_time", "expected_time"):
                    val = _get_ord_prop("delivery_time") or _get_ord_prop("expected_time")
                    if not val or str(val).strip() in ("", "---", "None"):
                        exp = _get_ord_prop("expected_time")
                        if exp:
                            val = exp.strftime("%H:%M") if isinstance(exp, datetime) else str(exp)
                        else:
                            val = "Ближайшее (ASAP)"

                elif field in ("total_with_discount", "final_price"):
                    val = _get_ord_prop("total_with_discount") or _get_ord_prop("final_price")
                elif field in ("total_discount", "discount_sum"):
                    val = _get_ord_prop("total_discount") or _get_ord_prop("discount_sum")
                elif field in ("courier_notes", "notes", "courier_comment"):
                    val = _get_ord_prop("courier_notes") or _get_ord_prop("notes") or _get_ord_prop("additional_info")
                elif field in ("sbp_qr", "sbp_qr_url"):
                    val = _get_ord_prop("sbp_qr_url") or _get_ord_prop("sbp_qr")
                elif field == "sbp_pay_link":
                    val = _get_ord_prop("sbp_pay_link")
                else:
                    val = _get_ord_prop(field)

                if val is None:
                    return ""
                if isinstance(val, datetime):
                    return val.strftime('%d.%m.%Y %H:%M')
                return str(val)
            
            # Фолбэк на стандартный поиск
            parts = var_path.split('.')
            val = context
            for part in parts:
                if isinstance(val, dict):
                    val = val.get(part)
                elif hasattr(val, part):
                    val = getattr(val, part)
                else:
                    return match.group(0)
            
            if val is None:
                return "0" if "revenue" in var_path else ""
            if isinstance(val, datetime):
                from app.core.datetime_utils import to_local
                local_dt = to_local(val, "Asia/Yekaterinburg")
                return local_dt.strftime('%d.%m.%Y %H:%M')
            if isinstance(val, (int, float)) and ("revenue" in var_path or "amount" in var_path or "sum" in var_path):
                return f"{float(val):,.2f}".replace(",", " ").replace(".00", "")
            return str(val)

        pattern = re.compile(r'\{\{([^}]+)\}\}')
        return pattern.sub(replace_var, template_text)

    """Маршрутизатор уведомлений для Системных рассылок"""

    async def dispatch_event(self, event_type: str, message_text: str, **kwargs):
        # Если заказ перешел в статус Delivered или пришло событие доставки — сворачиваем отправленные сообщения курьерам
        if event_type in ("order_delivered", "delivery_delivered"):
            order_kw = kwargs.get("order") or kwargs.get("order_context")
            order_kw_id = getattr(order_kw, "id", None) if order_kw else kwargs.get("order_id")
            if order_kw_id:
                try:
                    await collapse_order_notifications_on_delivery(int(order_kw_id))
                except Exception as c_err:
                    logger.warning(f"Error auto-collapsing delivery notifications: {c_err}")
        """
        Основной метод для отправки системного события.
        Находит всех активных подписчиков и распределяет сообщения по выбранным каналам.
        Поддерживает режимы адресации target_mode:
        - 'all': отправка всем подписанным сотрудникам
        - 'assigned_only': отправка только назначенному на заказ курьеру/сотруднику
        - 'assigned_and_admins': отправка назначенному сотруднику + администраторам/управляющим
        """
        logger.info(f"Dispatching notification event: {event_type}")
        import json
        
        def is_courier_assigned_to_order(acc, ord_obj, sess) -> bool:
            if not ord_obj:
                return False
            c_name = None
            c_iiko_id = None
            c_phone = None
            if isinstance(ord_obj, dict):
                c_name = ord_obj.get("courier_name")
                c_iiko_id = ord_obj.get("courier_iiko_id")
                c_phone = ord_obj.get("courier_phone")
            else:
                c_name = getattr(ord_obj, "courier_name", None)
                c_iiko_id = getattr(ord_obj, "courier_iiko_id", None)
                c_phone = getattr(ord_obj, "courier_phone", None)

            if not c_name or str(c_name).strip() in ("Не назначен", "---", ""):
                return False

            clean_c_name = str(c_name).strip().lower()
            target_words = {w for w in clean_c_name.split() if len(w) > 2 and w not in ["курьер", "courier"]}

            # 1. Сверка по имени аккаунта
            if acc.name:
                acc_name = acc.name.strip().lower()
                if acc_name == clean_c_name or acc_name in clean_c_name or clean_c_name in acc_name:
                    return True
                acc_words = {w for w in acc_name.split() if len(w) > 2 and w not in ["курьер", "courier"]}
                if target_words and acc_words and (target_words & acc_words):
                    return True

            # 2. Сверка по привязанному сотруднику
            from app.models.employee import Employee
            if acc.employee_id:
                employee = sess.get(Employee, acc.employee_id)
                if employee:
                    # 2.1. Точное сопоставление по iiko_id сотрудника
                    if c_iiko_id and employee.iiko_id and str(employee.iiko_id) == str(c_iiko_id):
                        return True
                    # 2.2. Сопоставление по имени сотрудника
                    if employee.name:
                        emp_name = employee.name.strip().lower()
                        if emp_name == clean_c_name or emp_name in clean_c_name or clean_c_name in emp_name:
                            return True
                        emp_words = {w for w in emp_name.split() if len(w) > 2 and w not in ["курьер", "courier"]}
                        if target_words and emp_words and (target_words & emp_words):
                            return True

            # 3. Сверка по прямому телефону курьера из заказа (если передан)
            if c_phone and (acc.phone or getattr(acc, "employee_id", None)):
                import re
                p_order = re.sub(r"\D", "", str(c_phone))[-10:]
                if acc.phone:
                    p_acc = re.sub(r"\D", "", str(acc.phone))[-10:]
                    if p_order and p_acc and p_order == p_acc:
                        return True

            # 4. Поиск назначенного курьера в таблице Employee и сверка с текущим аккаунтом
            assigned_emp = None
            if c_iiko_id:
                assigned_emp = sess.exec(select(Employee).where(Employee.iiko_id == str(c_iiko_id))).first()
            if not assigned_emp and clean_c_name:
                assigned_emp = sess.exec(select(Employee).where(Employee.name.ilike(f"%{c_name}%"))).first()

            if assigned_emp:
                if acc.employee_id and acc.employee_id == assigned_emp.id:
                    return True
                if assigned_emp.phone and acc.phone:
                    import re
                    p1 = re.sub(r"\D", "", str(assigned_emp.phone))[-10:]
                    p2 = re.sub(r"\D", "", str(acc.phone))[-10:]
                    if p1 and p2 and p1 == p2:
                        return True

            return False

        def is_admin_or_manager(acc, sess) -> bool:
            if acc.employee_id:
                from app.models.employee import Employee
                emp = sess.get(Employee, acc.employee_id)
                if emp and (emp.is_admin or (emp.role and any(r in emp.role.lower() for r in ["админ", "управл", "менедж", "директор", "руковод"]))):
                    return True
            if getattr(acc, "user_id", None):
                from app.models.user import User
                usr = sess.get(User, acc.user_id)
                if usr and (usr.is_superuser or (usr.role and any(r in usr.role.name.lower() for r in ["админ", "управл", "менедж", "директор", "руковод", "admin"]))):
                    return True
            if hasattr(acc, "groups") and acc.groups:
                for grp in acc.groups:
                    if grp.name and any(r in grp.name.lower() for r in ["админ", "управл", "менедж", "руковод"]):
                        return True
            # Проверка имени самого системного аккаунта VkBotAccount
            if getattr(acc, "name", None):
                acc_name_low = acc.name.lower()
                if any(r in acc_name_low for r in ["админ", "управл", "менедж", "директор", "руковод", "шеф", "admin"]):
                    return True
            return False

        with Session(engine) as session:
            # Ищем шаблон для этого события
            template = session.exec(
                select(VkTemplate).where(VkTemplate.event_type == event_type)
            ).first()

            # Шаг 0 цепочки: Проверка активности шаблона
            if template and not getattr(template, "is_active", True):
                logger.info(f"Notification for event '{event_type}' is disabled (is_active=False). Skipping.")
                return
            
            context_data = kwargs.get("context_data") or kwargs.get("context") or {}
            order_context = context_data.get("order") if context_data else None
            chain_flags = context_data.get("chain_flags", {}) if context_data else {}
            is_reassigned = kwargs.get("is_reassigned") or chain_flags.get("is_reassigned", False)
            is_amount_changed = kwargs.get("is_amount_changed") or chain_flags.get("is_amount_changed", False)
            is_address_changed = kwargs.get("is_address_changed") or chain_flags.get("is_address_changed", False)
            is_time_changed = kwargs.get("is_time_changed") or chain_flags.get("is_time_changed", False)
            is_cooking_time_set = kwargs.get("is_cooking_time_set") or chain_flags.get("is_cooking_time_set", False)
            is_cooking_time_rechanged = kwargs.get("is_cooking_time_rechanged") or chain_flags.get("is_cooking_time_rechanged", False)

            def _normalize_status(val: Any) -> str:
                if not val:
                    return ""
                if hasattr(val, "value"):
                    val = val.value
                s = str(val).strip().lower()
                if s.startswith("orderstatus."):
                    s = s[len("orderstatus."):]
                ru_map = {
                    "новый": "new",
                    "новый заказ": "new",
                    "не подтвержден": "unconfirmed",
                    "подтвержден": "confirmed",
                    "готовится": "cooking",
                    "в подготовке": "preparing",
                    "готов": "ready",
                    "готов к выдаче": "ready_for_pickup",
                    "в пути": "delivering",
                    "доставляется": "delivering",
                    "доставлен": "delivered",
                    "закрыт": "closed",
                    "отменен": "cancelled",
                    "отменен ❌": "cancelled",
                }
                return ru_map.get(s, s)

            # Объект заказа для проверок условий цепочки и назначения
            order = None
            if kwargs.get("order"):
                order = kwargs.get("order")
            elif context_data.get("order_obj"):
                order = context_data.get("order_obj")
            elif order_context:
                if isinstance(order_context, dict):
                    o_id = order_context.get("id") or order_context.get("order_id")
                    if o_id:
                        from app.models.order import Order
                        order = session.get(Order, int(o_id))
                elif hasattr(order_context, "id"):
                    order = order_context

            order_for_check = order if order else order_context

            def get_order_courier_name():
                if order_context and isinstance(order_context, dict):
                    c = order_context.get("courier_name")
                    if c and str(c).strip() not in ("", "Не назначен", "---"):
                        return str(c).strip()
                if order and hasattr(order, "courier_name"):
                    c = getattr(order, "courier_name", None)
                    if c and str(c).strip() not in ("", "Не назначен", "---"):
                        return str(c).strip()
                if order_for_check:
                    c = order_for_check.get("courier_name") if isinstance(order_for_check, dict) else getattr(order_for_check, "courier_name", None)
                    if c and str(c).strip() not in ("", "Не назначен", "---"):
                        return str(c).strip()
                return None

            def get_order_cooking_time_minutes() -> int:
                for obj in (order_context, order_for_check, order):
                    if not obj:
                        continue
                    val = obj.get("cooking_time_minutes") or obj.get("cooking_time") if isinstance(obj, dict) else (getattr(obj, "cooking_time_minutes", None) or getattr(obj, "cooking_time", None))
                    if val is not None:
                        try:
                            import re
                            m = re.search(r"\d+", str(val))
                            if m:
                                mins = int(m.group(0))
                                if mins > 0:
                                    return mins
                        except Exception:
                            pass
                    if not isinstance(obj, dict) and getattr(obj, "cooking_time_updated_at", None):
                        return 1
                return 0

            # Шаг 1 цепочки: Разбор параметров chain_config (Логическая цепочка проверок)
            chain_config_obj = {}
            if template and template.chain_config:
                try:
                    import json
                    if isinstance(template.chain_config, str):
                        chain_config_obj = json.loads(template.chain_config)
                    elif isinstance(template.chain_config, dict):
                        chain_config_obj = template.chain_config
                except Exception as c_err:
                    logger.warning(f"Failed to parse chain_config for '{event_type}': {c_err}")

            # 1.1. Проверка требования: назначен ли курьер
            if chain_config_obj.get("require_courier_assigned"):
                c_name = get_order_courier_name()
                if not c_name or str(c_name).strip() in ("", "Не назначен", "---"):
                    logger.info(f"Skipping notification for '{event_type}': chain requires assigned courier, but no courier assigned")
                    return

            # 1.2. Проверка требования: было ли установлено время приготовления кухни (>0 мин)
            # Активировать отправку уведомления только после установления времени кухни!
            cooking_check_events = ("courier_assigned", "courier_reassigned", "order_delivering", "order_delivered")
            require_cooking_set = chain_config_obj.get("require_cooking_time_set")
            if require_cooking_set is None and event_type in cooking_check_events:
                require_cooking_set = True

            if require_cooking_set:
                cook_mins = get_order_cooking_time_minutes()
                if cook_mins <= 0:
                    logger.info(f"Skipping notification for '{event_type}': chain requires cooking time to be set (>0), but it is {cook_mins}")
                    return

            # 1.3. Проверка требования: строго повторное изменение времени кухни (первичная установка не отправляется!)
            if chain_config_obj.get("require_cooking_time_changed"):
                if not is_cooking_time_rechanged:
                    logger.info(f"Skipping notification for '{event_type}': chain requires repeated cooking time change, but it is not a repeated change (is_cooking_time_rechanged={is_cooking_time_rechanged})")
                    return

            # 1.4. Проверка требования: изменение суммы заказа
            if chain_config_obj.get("require_amount_changed"):
                if not is_amount_changed and event_type == "order_amount_changed":
                    logger.info(f"Skipping notification for '{event_type}': chain requires amount to be changed, but is_amount_changed is False")
                    return

            # 1.5. Проверка требования: изменение адреса доставки
            if chain_config_obj.get("require_address_changed"):
                if not is_address_changed and event_type == "order_address_changed":
                    logger.info(f"Skipping notification for '{event_type}': chain requires address to be changed, but is_address_changed is False")
                    return

            # 1.6. Проверка требования: изменение времени доставки
            if chain_config_obj.get("require_time_changed"):
                if not is_time_changed and event_type == "order_time_changed":
                    logger.info(f"Skipping notification for '{event_type}': chain requires delivery time to be changed, but is_time_changed is False")
                    return

            # 1.7. Проверка требования: только для неоплаченных заказов
            if chain_config_obj.get("only_unpaid"):
                is_paid = False
                if order_context:
                    if isinstance(order_context, dict):
                        is_paid = order_context.get("is_paid_bool") or (order_context.get("is_paid") in ("Оплачен", True))
                    else:
                        is_paid = getattr(order_context, "is_paid", False)
                if is_paid:
                    logger.info(f"Skipping notification for '{event_type}': chain requires order to be unpaid, but order is paid")
                    return

            # 1.8. Проверка фильтра целевых статусов заказа (объединяем include_statuses и chain_config.check_status_in)
            allowed_statuses = []
            if chain_config_obj.get("check_status_in") and isinstance(chain_config_obj.get("check_status_in"), list):
                allowed_statuses.extend(chain_config_obj.get("check_status_in"))
            if template and template.include_statuses:
                try:
                    import json
                    parsed_inc = json.loads(template.include_statuses)
                    if isinstance(parsed_inc, list):
                        for s in parsed_inc:
                            if s not in allowed_statuses:
                                allowed_statuses.append(s)
                except Exception as inc_err:
                    logger.warning(f"Error evaluating include_statuses: {inc_err}")

            if allowed_statuses:
                curr_status = None
                if order_context:
                    if isinstance(order_context, dict):
                        curr_status = order_context.get("raw_status") or order_context.get("status")
                    else:
                        curr_status = getattr(order_context, "status", None)
                norm_curr = _normalize_status(curr_status)
                norm_allowed = [_normalize_status(st) for st in allowed_statuses]
                status_matched = norm_curr in norm_allowed or any(st == norm_curr or st in norm_curr or norm_curr in st for st in norm_allowed if st)
                if not status_matched:
                    logger.info(f"Skipping notification for '{event_type}': normalized status '{norm_curr}' is not in allowed chain statuses ({norm_allowed})")
                    return

            # 1.9. Проверка повтора при переназначении курьера
            if is_reassigned and "resend_on_courier_reassigned" in chain_config_obj:
                if not chain_config_obj.get("resend_on_courier_reassigned"):
                    logger.info(f"Skipping notification for '{event_type}': courier was reassigned, but resend_on_courier_reassigned is False")
                    return

            target_mode = (template.target_mode if template and template.target_mode else "all").strip().lower()
            attach_qr_by_template = bool(
                getattr(template, "attach_sbp_qr", False) or chain_config_obj.get("attach_sbp_qr", False)
            )

            # Определение канала отправки ВКонтакте:
            # Для курьеров — сообщество/бот курьеров (ID=2 или выбранный в шаге)
            # Для обычных шаблонов — основное сообщество, выбранное в "Настройки каналов" (is_main=True)
            template_bot_token = None
            courier_events = {
                "order_new", "courier_assigned", "change_cooking_time", 
                "order_status_update", "order_amount_changed", "order_items_changed", 
                "order_address_changed", "order_time_changed", "order_cancelled"
            }
            from app.models.vk_bot_connection import VkBotConnection
            target_bot = None

            if template and getattr(template, "vk_bot_id", None):
                target_bot = session.get(VkBotConnection, template.vk_bot_id)
            elif event_type in courier_events:
                target_bot = session.get(VkBotConnection, 2)
                if not target_bot or not target_bot.is_active:
                    from sqlmodel import or_
                    target_bot = session.exec(select(VkBotConnection).where(
                        VkBotConnection.is_active == True,
                        or_(VkBotConnection.name.ilike("%курьер%"), VkBotConnection.name.ilike("%courier%"))
                    )).first()

            # Если бот не определен или для обычных шаблонов — берем выбранный основной бот из "Настройки каналов"
            if not target_bot or not target_bot.is_active:
                target_bot = session.exec(select(VkBotConnection).where(
                    VkBotConnection.is_main == True, 
                    VkBotConnection.is_active == True
                )).first()

            if target_bot and target_bot.vk_bot_token:
                template_bot_token = target_bot.vk_bot_token
                logger.debug(f"Selected VK bot '{target_bot.name}' (ID: {target_bot.id}) for event '{event_type}'")

            # Каналы отправки, настроенные на уровне шаблона
            tpl_send_vk = getattr(template, "send_vk", True) if template else True
            tpl_send_tg = getattr(template, "send_tg", False) if template else False
            tpl_send_max = getattr(template, "send_max", False) if template else False
            tpl_send_sms = getattr(template, "send_sms", False) if template else False

            # Ищем подписки на это событие (активные получатели)
            statement = (
                select(VkBotSubscription, VkBotAccount)
                .join(VkBotAccount)
                .where(VkBotSubscription.event_type == event_type)
                .where(VkBotAccount.is_active == True)
            )
            results = list(session.exec(statement).all())
            subscribed_acc_ids = {acc.id for _, acc in results}

            from app.core.datetime_utils import get_tz_name, get_local_now, utc_now
            current_hour = get_local_now(get_tz_name(session)).hour
            tg_token = get_telegram_token(session)

            # Гарантированная адресация назначенному курьеру заказа:
            # Выполняется СТРОГО для курьерских событий («Цепочки курьера»)!
            if event_type in courier_events and (order_context or order_for_check):
                all_courier_accs = session.exec(
                    select(VkBotAccount).where(VkBotAccount.is_courier == True, VkBotAccount.is_active == True)
                ).all()
                for c_acc in all_courier_accs:
                    if not getattr(c_acc, "allow_courier_chains", True):
                        continue
                    if c_acc.id not in subscribed_acc_ids and is_courier_assigned_to_order(c_acc, order_context or order_for_check, session):
                        synthetic_sub = VkBotSubscription(
                            account_id=c_acc.id,
                            event_type=event_type,
                            delivery_mode=DeliveryMode.REALTIME,
                            active_start_hour=0,
                            active_end_hour=23,
                            send_vk=getattr(c_acc, "courier_chains_vk", c_acc.use_vk),
                            send_tg=getattr(c_acc, "courier_chains_tg", c_acc.use_tg),
                            send_max=getattr(c_acc, "courier_chains_max", c_acc.use_max),
                            send_sms=getattr(c_acc, "courier_chains_sms", c_acc.use_sms)
                        )
                        results.append((synthetic_sub, c_acc))
                        subscribed_acc_ids.add(c_acc.id)
                        logger.info(f"Auto-included assigned courier {c_acc.name} (ID: {c_acc.id}) into recipients for courier event '{event_type}'")

            # Автоматическое включение конкретных получателей, указанных в шаблоне (target_mode == 'specific')
            if target_mode in ("specific", "by_accounts") and template and getattr(template, "target_accounts", None):
                target_ids = []
                try:
                    if isinstance(template.target_accounts, list):
                        target_ids = [int(x) for x in template.target_accounts]
                    elif isinstance(template.target_accounts, str):
                        target_ids = [int(x) for x in json.loads(template.target_accounts) if str(x).isdigit()]
                except Exception:
                    try:
                        target_ids = [int(x.strip()) for x in str(template.target_accounts).split(",") if x.strip().isdigit()]
                    except Exception:
                        target_ids = []
                
                for t_acc_id in target_ids:
                    if t_acc_id not in subscribed_acc_ids:
                        t_acc = session.get(VkBotAccount, t_acc_id)
                        if t_acc and t_acc.is_active:
                            synthetic_sub = VkBotSubscription(
                                account_id=t_acc.id,
                                event_type=event_type,
                                delivery_mode=DeliveryMode.REALTIME,
                                active_start_hour=0,
                                active_end_hour=23,
                                send_vk=getattr(t_acc, "use_vk", True),
                                send_tg=getattr(t_acc, "use_tg", False),
                                send_max=getattr(t_acc, "use_max", False),
                                send_sms=getattr(t_acc, "use_sms", False)
                            )
                            results.append((synthetic_sub, t_acc))
                            subscribed_acc_ids.add(t_acc.id)
                            logger.info(f"Auto-included specific recipient {t_acc.name} (ID: {t_acc.id}) for event '{event_type}'")

            # Проверяем, есть ли необходимость формирования QR-кода
            has_qr_receivers = attach_qr_by_template or any(getattr(account, "send_payment_qr", False) for sub, account in results)
            
            qr_file_path = None
            public_qr_url = None
            
            if has_qr_receivers and order_context:
                curr_order_id = getattr(order, "id", None) if order else (order_context.get("id") if isinstance(order_context, dict) else getattr(order_context, "id", None))
                if curr_order_id:
                    # 1. Проверяем тип заказа: исключаем Самовывоз (для самовывоза курьерский QR не нужен)
                    ord_type = str(getattr(order, "order_type", "") or (order_context.get("order_type") if isinstance(order_context, dict) else "")).lower()
                    is_pickup = "самовывоз" in ord_type or "pickup" in ord_type

                    # 2. Проверяем способ оплаты и признак постоплаты курьеру
                    pay_method = str(getattr(order, "payment_method", "") or (order_context.get("payment_method") if isinstance(order_context, dict) else "")).lower()
                    is_courier_payment = any(w in pay_method for w in ("курьер", "наличн", "cash"))
                    is_online_prepaid = any(w in pay_method for w in ("t bank", "chibis", "онлайн", "online", "сайт"))

                    # Статус оплаты в БД / iiko
                    is_order_paid = bool(getattr(order, "is_paid", False)) if order else False
                    if isinstance(order_context, dict) and order_context.get("is_paid") in ("Оплачен", True):
                        is_order_paid = True

                    # Требование цепочки: "только неоплаченные"
                    require_only_unpaid = bool(chain_config_obj.get("only_unpaid", False))

                    # Условие пропуска:
                    # - Самовывоз пропускаем всегда.
                    # - Если включена опция "только неоплаченные" (require_only_unpaid):
                    #     * если онлайн-предоплата (Т-Банк/Чибис/Сайт) и заказ оплачен -> пропускаем.
                    #     * если заказ оплачен и это НЕ оплата курьеру -> пропускаем.
                    #     * при способе оплаты курьеру/наличными (постоплата) QR нужен курьеру для расчета!
                    skip_qr = False
                    if is_pickup:
                        skip_qr = True
                    elif require_only_unpaid:
                        if is_online_prepaid and is_order_paid:
                            skip_qr = True
                        elif is_order_paid and not is_courier_payment:
                            skip_qr = True

                    if not skip_qr:
                        amount = 0.0
                        if getattr(order, "left_to_pay", None) and float(order.left_to_pay) > 0:
                            amount = float(order.left_to_pay)
                        elif getattr(order, "payments_details", None) and isinstance(order.payments_details, dict):
                            for p_item in order.payments_details.get("items", []):
                                p_name = str(p_item.get("name", "")).lower()
                                if any(w in p_name for w in ("курьер", "наличн", "картой", "сбп")) and float(p_item.get("sum", 0)) > 0:
                                    amount = float(p_item.get("sum"))
                                    break
                        if amount <= 0:
                            if getattr(order, "total_with_discount", None) and float(order.total_with_discount) > 0:
                                amount = float(order.total_with_discount)
                            elif getattr(order, "total_amount", None) and float(order.total_amount) > 0:
                                amount = float(order.total_amount)
                            elif isinstance(order_context, dict):
                                try:
                                    amount = float(order_context.get("total_with_discount") or order_context.get("total_amount") or 0)
                                except:
                                    amount = 0.0

                        if amount > 0:
                            order_num = str((order.external_number if order else None) or (order_context.get("external_number") if isinstance(order_context, dict) else None) or curr_order_id)
                            addr_str = str((order.delivery_address if order else None) or (order_context.get("delivery_address") if isinstance(order_context, dict) else None) or "---")
                            qr_file_path = await generate_sbp_qr_image(curr_order_id, amount, session, order_number=order_num, delivery_address=addr_str)
                            if qr_file_path:
                                import os
                                public_qr_url = f"https://vezuroll.ru/media/img/qr/{os.path.basename(qr_file_path)}"
                                if isinstance(context_data.get("order"), dict):
                                    context_data["order"]["sbp_qr_url"] = public_qr_url
                                    context_data["order"]["sbp_qr"] = public_qr_url
                                elif hasattr(context_data.get("order"), "__dict__"):
                                    setattr(context_data["order"], "sbp_qr_url", public_qr_url)
                                    setattr(context_data["order"], "sbp_qr", public_qr_url)
                                context_data["sbp_qr_url"] = public_qr_url
                                context_data["sbp_qr"] = public_qr_url

            # Рендеринг шаблона с обновленным контекстом (включая QR ссылку)
            if template:
                rendered_text = self.render_template(template.text, context_data)
                keyboard = template.keyboard_json
                tg_keyboard = None
                if template.keyboard_telegram:
                    try:
                        tg_keyboard = json.loads(template.keyboard_telegram)
                    except Exception as e:
                        logger.warning(f"Failed to parse keyboard_telegram JSON: {e}")
            else:
                rendered_text = message_text
                keyboard = None
                tg_keyboard = None

            # Кэш отправленных сообщений в рамках текущего события для предотвращения дублирования
            # при привязке одинаковых страниц (VK / Telegram / MAX) нескольким получателям
            sent_vk_results = {}   # vk_user_id -> vk_res
            sent_tg_results = {}   # tg_user_id -> bool (success)
            sent_max_results = {}  # target -> bool (success)

            for sub, account in results:
                # 0. Строгая изоляция курьерских цепочек («Цепочки курьера»)
                if event_type in courier_events:
                    # 0.1. Получатель ОБЯЗАН быть курьером!
                    is_courier_user = getattr(account, "is_courier", False) or is_courier_assigned_to_order(account, order_context or order_for_check, session)
                    if not is_courier_user:
                        logger.debug(f"Skipping courier event '{event_type}' for {account.name}: not a courier")
                        continue

                    # 0.2. Проверка разрешения получения цепочек курьера
                    if not getattr(account, "allow_courier_chains", True):
                        logger.debug(f"Skipping courier event '{event_type}' for {account.name}: allow_courier_chains is False")
                        continue

                    # 0.3. Режим адресации target_mode для цепочек курьера:
                    c_name_check = get_order_courier_name()
                    if target_mode == "assigned_only":
                        if not c_name_check:
                            logger.debug(f"Skipping courier event '{event_type}' for {account.name}: target_mode='assigned_only' but no courier assigned")
                            continue
                        if not is_courier_assigned_to_order(account, order_context or order_for_check, session):
                            logger.debug(f"Skipping courier event '{event_type}' for {account.name}: not the assigned courier ({c_name_check})")
                            continue
                    elif target_mode == "assigned_and_admins":
                        is_assigned = is_courier_assigned_to_order(account, order_context or order_for_check, session)
                        is_admin = is_admin_or_manager(account, session)
                        if not (is_assigned or is_admin):
                            logger.debug(f"Skipping courier event '{event_type}' for {account.name}: target_mode='assigned_and_admins' and not assigned/admin")
                            continue
                    elif target_mode in ("specific", "by_accounts"):
                        allowed_acc_ids = []
                        if template and getattr(template, "target_accounts", None):
                            try:
                                if isinstance(template.target_accounts, list):
                                    allowed_acc_ids = [int(x) for x in template.target_accounts]
                                elif isinstance(template.target_accounts, str):
                                    allowed_acc_ids = [int(x) for x in json.loads(template.target_accounts) if str(x).isdigit()]
                            except Exception:
                                allowed_acc_ids = [int(x.strip()) for x in str(template.target_accounts).split(",") if x.strip().isdigit()]
                        if allowed_acc_ids and account.id not in allowed_acc_ids:
                            logger.debug(f"Skipping courier event '{event_type}' for {account.name}: not in target_accounts")
                            continue
                    else:
                        # target_mode == 'all': если курьер назначен, отправляем назначенному
                        if c_name_check and not is_courier_assigned_to_order(account, order_context or order_for_check, session):
                            logger.debug(f"Skipping courier event '{event_type}' for {account.name}: not the assigned courier ({c_name_check})")
                            continue
                else:
                    # 0. Проверка режима адресации шаблона для сотрудников (target_mode)
                    if target_mode == "assigned_only":
                        if not is_courier_assigned_to_order(account, order_for_check, session):
                            logger.debug(f"Skipping notification for {account.name}: target_mode='assigned_only' and courier not matching")
                            continue
                    elif target_mode == "assigned_and_admins":
                        is_assigned = is_courier_assigned_to_order(account, order_for_check, session)
                        is_admin = is_admin_or_manager(account, session)
                        if not (is_assigned or is_admin):
                            logger.debug(f"Skipping notification for {account.name}: target_mode='assigned_and_admins' and employee is neither assigned nor admin")
                            continue
                    elif target_mode in ("roles", "by_roles"):
                        allowed_roles = []
                        if template and getattr(template, "target_roles", None):
                            try:
                                if isinstance(template.target_roles, list):
                                    allowed_roles = template.target_roles
                                elif isinstance(template.target_roles, str):
                                    allowed_roles = json.loads(template.target_roles)
                            except Exception:
                                allowed_roles = [r.strip() for r in str(template.target_roles).split(",") if r.strip()]
                        
                        if allowed_roles:
                            acc_roles = set()
                            if account.employee_id:
                                from app.models.employee import Employee
                                emp = session.get(Employee, account.employee_id)
                                if emp and emp.role:
                                    acc_roles.add(emp.role.strip().lower())
                                if emp and emp.is_courier:
                                    acc_roles.add("курьер")
                                    acc_roles.add("courier")
                                if emp and emp.is_admin:
                                    acc_roles.add("администратор")
                                    acc_roles.add("admin")
                            if getattr(account, "is_courier", False):
                                acc_roles.add("курьер")
                                acc_roles.add("courier")
                            if getattr(account, "user_id", None):
                                from app.models.user import User
                                u = session.get(User, account.user_id)
                                if u and u.role and u.role.name:
                                    acc_roles.add(u.role.name.strip().lower())
                            if hasattr(account, "groups") and account.groups:
                                for grp in account.groups:
                                    if grp.name:
                                        acc_roles.add(grp.name.strip().lower())
                            if getattr(account, "name", None):
                                acc_name_low = account.name.lower()
                                for r_kw in ["курьер", "повар", "админ", "управл", "менедж", "оператор"]:
                                    if r_kw in acc_name_low:
                                        acc_roles.add(r_kw)
                            
                            clean_allowed = {str(r).strip().lower() for r in allowed_roles}
                            matched = False
                            for ar in acc_roles:
                                for cr in clean_allowed:
                                    if ar == cr or cr in ar or ar in cr:
                                        matched = True
                                        break
                                if matched:
                                    break
                            if not matched:
                                logger.debug(f"Skipping notification for {account.name}: roles {acc_roles} not in target_roles {clean_allowed}")
                                continue

                    elif target_mode in ("specific", "by_accounts"):
                        allowed_accs = []
                        if template and getattr(template, "target_accounts", None):
                            try:
                                if isinstance(template.target_accounts, list):
                                    allowed_accs = [int(x) for x in template.target_accounts]
                                elif isinstance(template.target_accounts, str):
                                    allowed_accs = [int(x) for x in json.loads(template.target_accounts)]
                            except Exception:
                                allowed_accs = []
                        if allowed_accs and (account.id not in allowed_accs and (not account.employee_id or account.employee_id not in allowed_accs)):
                            logger.debug(f"Skipping notification for {account.name}: account {account.id} not in target_accounts {allowed_accs}")
                            continue

                # Проверка диапазона активности
                is_active_hour = False
                if sub.active_start_hour <= sub.active_end_hour:
                    is_active_hour = sub.active_start_hour <= current_hour <= sub.active_end_hour
                else:
                    is_active_hour = current_hour >= sub.active_start_hour or current_hour <= sub.active_end_hour

                if not is_active_hour:
                    logger.debug(f"Skipping notification for {account.name}: outside active hours ({sub.active_start_hour}-{sub.active_end_hour})")
                    continue

                # Определяем, нужно ли отправлять QR-код этому получателю
                should_send_qr = False
                if qr_file_path:
                    if attach_qr_by_template:
                        should_send_qr = True
                    elif getattr(account, "send_payment_qr", False):
                        qr_mode = getattr(account, "payment_qr_mode", "all")
                        if qr_mode == "all":
                            should_send_qr = True
                        elif qr_mode == "assigned_only":
                            should_send_qr = is_courier_assigned_to_order(account, order_for_check, session)

                # Флаг: относится ли получатель к курьерам заказа
                is_courier_recipient = bool(
                    order and (is_courier_assigned_to_order(account, order_for_check, session) or getattr(account, "is_courier", False))
                )

                # Определение эффективных каналов для события
                eff_send_vk = getattr(account, "courier_chains_vk", sub.send_vk) if event_type in courier_events else sub.send_vk
                eff_send_tg = getattr(account, "courier_chains_tg", sub.send_tg) if event_type in courier_events else sub.send_tg
                eff_send_max = getattr(account, "courier_chains_max", sub.send_max) if event_type in courier_events else sub.send_max
                eff_send_sms = getattr(account, "courier_chains_sms", sub.send_sms) if event_type in courier_events else sub.send_sms

                is_courier_cascade = bool(is_courier_recipient and event_type in courier_events)
                is_vk_ok = False
                is_tg_ok = False

                # 1. ВКонтакте
                if tpl_send_vk and eff_send_vk and (account.use_vk or event_type in courier_events) and account.vk_user_id:
                    if sub.delivery_mode == DeliveryMode.REALTIME:
                        cache_key_vk = (account.vk_user_id, should_send_qr)
                        action_kb = build_courier_action_keyboards(order) if (is_courier_recipient and order) else None
                        eff_vk_kb = action_kb["vk"] if (action_kb and getattr(template, "show_courier_action_buttons", True) and not keyboard) else keyboard
                        
                        vk_edit_done = False
                        if getattr(template, "edit_existing_message", True) and is_courier_recipient and order and getattr(order, "id", None):
                            ex_vk = session.exec(
                                select(CourierOrderNotification)
                                .where(CourierOrderNotification.order_id == order.id)
                                .where(CourierOrderNotification.account_id == account.id)
                                .where(CourierOrderNotification.channel == "vk")
                                .where(CourierOrderNotification.is_collapsed == False)
                                .where(CourierOrderNotification.external_message_id != None)
                            ).first()
                            if ex_vk and ex_vk.external_message_id:
                                try:
                                    curr_att = ex_vk.qr_attachment_id
                                    if should_send_qr and qr_file_path and not curr_att:
                                        from app.services.vk_service import upload_vk_photo_detailed
                                        target_t = template_bot_token or vk_bot_service._get_bot_token()
                                        new_att, _ = await upload_vk_photo_detailed(target_t, qr_file_path, account.vk_user_id)
                                        if new_att:
                                            curr_att = new_att
                                            ex_vk.qr_attachment_id = new_att
                                            session.add(ex_vk)

                                    edit_res = await vk_bot_service.edit_message(
                                        peer_id=account.vk_user_id,
                                        message_id=int(ex_vk.external_message_id),
                                        message=rendered_text,
                                        attachment=curr_att or "",
                                        keyboard=eff_vk_kb,
                                        bot_token_override=template_bot_token
                                    )
                                    if edit_res.get("success"):
                                        vk_edit_done = True
                                        ex_vk.sent_at = utc_now()
                                        session.add(ex_vk)
                                except Exception as e_vedit:
                                    logger.warning(f"Error editing VK courier message: {e_vedit}")

                        if vk_edit_done:
                            vk_res = {"success": True, "edited": True}
                        elif cache_key_vk not in sent_vk_results:
                            acc_msg = rendered_text
                            vk_res = await vk_bot_service.send_message(
                                user_id=account.vk_user_id,
                                message=acc_msg,
                                keyboard=eff_vk_kb,
                                account_id=account.id,
                                event_type=event_type,
                                image_path=qr_file_path if should_send_qr else None,
                                bot_token_override=template_bot_token
                            )
                            sent_vk_results[cache_key_vk] = vk_res or {}
                        else:
                            vk_res = sent_vk_results[cache_key_vk]
                            logger.info(f"Re-using already sent VK notification for shared vk_user_id={account.vk_user_id} (recipient account {account.id})")
                            shared_log = VkBotMessageLog(
                                account_id=account.id,
                                text=acc_msg,
                                event_type=event_type,
                                status=MessageStatus.SENT if (vk_res and vk_res.get("success")) else MessageStatus.FAILED,
                                error_text=vk_res.get("error") if vk_res else None,
                                sent_at=utc_now() if (vk_res and vk_res.get("success")) else None
                            )
                            session.add(shared_log)

                        is_vk_ok = bool(vk_res and vk_res.get("success"))
                        if is_vk_ok:
                            if not account.is_verified:
                                account.is_verified = True
                                session.add(account)
                        elif vk_res and vk_res.get("error_code") == 901:
                            if account.is_verified:
                                account.is_verified = False
                                session.add(account)

                        if is_courier_recipient and order:
                            c_stat = "unread" if is_vk_ok else "failed"
                            if order.courier_notification_status != "accepted":
                                order.courier_notification_status = c_stat
                                order.courier_notification_channel = "vk"
                                if not is_vk_ok:
                                    order.courier_last_message_text = f"Ошибка VK: {vk_res.get('error')}"
                                else:
                                    order.courier_last_message_text = None
                                session.add(order)
                            if not vk_edit_done:
                                c_log = CourierOrderNotification(
                                    order_id=order.id,
                                    account_id=account.id,
                                    courier_name=account.name or order.courier_name,
                                    channel="vk",
                                    external_message_id=str(vk_res.get("vk_message_id")) if is_vk_ok else None,
                                    external_chat_id=str(account.vk_user_id),
                                    qr_attachment_id=vk_res.get("attachment") if should_send_qr else None,
                                    status=c_stat,
                                    error_text=vk_res.get("error") if not is_vk_ok else None,
                                    sent_at=utc_now() if is_vk_ok else None
                                )
                                session.add(c_log)
                            elif ex_vk:
                                ex_vk.status = c_stat
                                if curr_att:
                                    ex_vk.qr_attachment_id = curr_att
                                session.add(ex_vk)
                    else:
                        log_entry = VkBotMessageLog(
                            account_id=account.id,
                            text=f"[VK] {rendered_text}" + (f" [QR Active]" if should_send_qr else ""),
                            event_type=event_type,
                            status=MessageStatus.PENDING
                        )
                        session.add(log_entry)

                # 2. Telegram (??????: ???????????? ??? ???????, ???? ???????????? ????? ?? ??? ??????? ???????? ???????????)
                if not (is_courier_cascade and is_vk_ok) and tpl_send_tg and eff_send_tg and (account.use_tg or event_type in courier_events) and account.tg_user_id:
                    if sub.delivery_mode == DeliveryMode.REALTIME:
                        if tg_token:
                            cache_key_tg = (account.tg_user_id, should_send_qr)
                            action_kb = build_courier_action_keyboards(order) if (is_courier_recipient and order) else None
                            eff_tg_kb = action_kb["tg"] if (action_kb and getattr(template, "show_courier_action_buttons", True) and not tg_keyboard) else tg_keyboard

                            tg_edit_done = False
                            tg_mid = None
                            if getattr(template, "edit_existing_message", True) and is_courier_recipient and order and getattr(order, "id", None):
                                ex_tg = session.exec(
                                    select(CourierOrderNotification)
                                    .where(CourierOrderNotification.order_id == order.id)
                                    .where(CourierOrderNotification.account_id == account.id)
                                    .where(CourierOrderNotification.channel == "tg")
                                    .where(CourierOrderNotification.is_collapsed == False)
                                    .where(CourierOrderNotification.external_message_id != None)
                                ).first()
                                if ex_tg and ex_tg.external_message_id:
                                    try:
                                        tg_edit_res = await edit_telegram_courier_message(
                                            tg_token=tg_token,
                                            chat_id=str(account.tg_user_id),
                                            message_id=ex_tg.external_message_id,
                                            new_text=rendered_text,
                                            reply_markup=eff_tg_kb,
                                            remove_photo=False
                                        )
                                        if tg_edit_res.get("success"):
                                            tg_edit_done = True
                                            tg_mid = ex_tg.external_message_id
                                            ex_tg.sent_at = utc_now()
                                            session.add(ex_tg)
                                    except Exception as e_tedit:
                                        logger.warning(f"Error editing TG courier message: {e_tedit}")

                            if tg_edit_done:
                                success = True
                            elif cache_key_tg not in sent_tg_results:
                                tg_text = rendered_text
                                if should_send_qr:
                                    tg_send_res = await send_telegram_photo(account.tg_user_id, qr_file_path, tg_text, tg_token, reply_markup=eff_tg_kb)
                                else:
                                    tg_send_res = await send_telegram_message(account.tg_user_id, tg_text, tg_token, reply_markup=eff_tg_kb)
                                success = bool(isinstance(tg_send_res, dict) and tg_send_res.get("success"))
                                tg_mid = tg_send_res.get("message_id") if isinstance(tg_send_res, dict) else None
                                sent_tg_results[cache_key_tg] = success
                            else:
                                success = sent_tg_results[cache_key_tg]
                                logger.info(f"Re-using already sent TG notification for shared tg_user_id={account.tg_user_id} (recipient account {account.id})")
                            
                            is_tg_ok = success
                            if success and not account.is_tg_verified:
                                account.is_tg_verified = True
                                session.add(account)

                            log_entry = VkBotMessageLog(
                                account_id=account.id,
                                text=f"[TG] {rendered_text}" + (f" [QR Sent]" if should_send_qr else ""),
                                event_type=event_type,
                                status=MessageStatus.SENT if success else MessageStatus.FAILED,
                                error_text=None if success else "Failed to send via Telegram Bot API",
                                sent_at=utc_now() if success else None
                            )
                            session.add(log_entry)

                            if is_courier_recipient and order:
                                c_stat = "unread" if success else "failed"
                                if order.courier_notification_status != "accepted":
                                    order.courier_notification_status = c_stat
                                    order.courier_notification_channel = "tg"
                                    if not success:
                                        order.courier_last_message_text = "Ошибка Telegram Bot API"
                                    else:
                                        order.courier_last_message_text = None
                                    session.add(order)
                                c_log = CourierOrderNotification(
                                    order_id=order.id,
                                    account_id=account.id,
                                    courier_name=account.name or order.courier_name,
                                    channel="tg",
                                    external_message_id=str(tg_mid) if (success and tg_mid) else None,
                                    external_chat_id=str(account.tg_user_id),
                                    status=c_stat,
                                    error_text="Failed to send via Telegram Bot API" if not success else None,
                                    sent_at=utc_now() if success else None
                                )
                                session.add(c_log)
                        else:
                            logger.error("Telegram token is not configured")
                    else:
                        log_entry = VkBotMessageLog(
                            account_id=account.id,
                            text=f"[TG] {rendered_text}" + (f" [QR Active]" if should_send_qr else ""),
                            event_type=event_type,
                            status=MessageStatus.PENDING
                        )
                        session.add(log_entry)

                if is_courier_cascade and is_vk_ok:
                    logger.info(f"?????? '{account.name}' ??????? ??????????? ? ???????????? ?????? (?????????). ????????? ?????? Telegram ? MAX ?????????.")

                # 3. MAX Messenger (??????: ???????????? ??? ???????, ???? ??????????? ??? ?????????? ? ?? ??? Telegram)
                if not (is_courier_cascade and (is_vk_ok or is_tg_ok)) and tpl_send_max and eff_send_max and (account.use_max or event_type in courier_events) and (account.max_user_id or account.phone):
                    target = account.max_user_id or account.phone
                    max_text = rendered_text
                    action_kb = build_courier_action_keyboards(order) if (is_courier_recipient and order) else None
                    eff_max_kb = action_kb["max"] if (action_kb and getattr(template, "show_courier_action_buttons", True)) else None
                    
                    if sub.delivery_mode == DeliveryMode.REALTIME:
                        eff_bot_id = getattr(template, "max_bot_id", None) or getattr(account, "max_bot_id", None)
                        eff_mode = getattr(template, "max_send_mode", None) or getattr(account, "max_send_mode", None) or "cascade"
                        cache_key = f"{target}_{eff_bot_id}_{eff_mode}"
                        
                        max_edit_done = False
                        max_mid = None
                        if getattr(template, "edit_existing_message", True) and is_courier_recipient and order and getattr(order, "id", None):
                            ex_max = session.exec(
                                select(CourierOrderNotification)
                                .where(CourierOrderNotification.order_id == order.id)
                                .where(CourierOrderNotification.account_id == account.id)
                                .where(CourierOrderNotification.channel == "max")
                                .where(CourierOrderNotification.is_collapsed == False)
                                .where(CourierOrderNotification.external_message_id != None)
                            ).first()
                            if ex_max and ex_max.external_message_id:
                                try:
                                    from app.services.max_service import edit_max_message
                                    max_edit_res = await edit_max_message(
                                        message_id=ex_max.external_message_id,
                                        recipient=str(target),
                                        text=max_text,
                                        buttons=eff_max_kb,
                                        keep_image=True,
                                        session=session,
                                        bot_id=eff_bot_id
                                    )
                                    if max_edit_res.get("success"):
                                        max_edit_done = True
                                        max_mid = ex_max.external_message_id
                                        ex_max.sent_at = utc_now()
                                        session.add(ex_max)
                                except Exception as e_medit:
                                    logger.warning(f"Error editing MAX courier message: {e_medit}")

                        if max_edit_done:
                            success = True
                        elif cache_key not in sent_max_results:
                            max_res = await send_max_message_helper(
                                target=target, 
                                text=max_text, 
                                session=session,
                                bot_id=eff_bot_id,
                                prefer_channel=eff_mode,
                                image_path=qr_file_path if should_send_qr else None,
                                buttons=eff_max_kb
                            )
                            success = bool(isinstance(max_res, dict) and max_res.get("success"))
                            max_mid = max_res.get("msg_id") if isinstance(max_res, dict) else None
                            sent_max_results[cache_key] = success
                        else:
                            success = sent_max_results[cache_key]
                            logger.info(f"Re-using already sent MAX notification for shared target={target} (recipient account {account.id})")

                        if success and not account.is_max_verified:
                            account.is_max_verified = True
                            session.add(account)

                        log_entry = VkBotMessageLog(
                            account_id=account.id,
                            text=f"[MAX] {max_text}",
                            event_type=event_type,
                            status=MessageStatus.SENT if success else MessageStatus.FAILED,
                            error_text=None if success else "Failed to send via MAX API",
                            sent_at=utc_now() if success else None
                        )
                        session.add(log_entry)

                        if is_courier_recipient and order:
                            c_stat = "unread" if success else "failed"
                            if order.courier_notification_status != "accepted":
                                order.courier_notification_status = c_stat
                                order.courier_notification_channel = "max"
                                if not success:
                                    order.courier_last_message_text = "Ошибка MAX API"
                                else:
                                    order.courier_last_message_text = None
                                session.add(order)
                            c_log = CourierOrderNotification(
                                order_id=order.id,
                                account_id=account.id,
                                courier_name=account.name or order.courier_name,
                                channel="max",
                                external_message_id=str(max_mid) if (success and max_mid) else None,
                                external_chat_id=str(target),
                                bot_id=eff_bot_id,
                                status=c_stat,
                                error_text="Failed to send via MAX API" if not success else None,
                                sent_at=utc_now() if success else None
                            )
                            session.add(c_log)
                    else:
                        log_entry = VkBotMessageLog(
                            account_id=account.id,
                            text=f"[MAX] {max_text}",
                            event_type=event_type,
                            status=MessageStatus.PENDING
                        )
                        session.add(log_entry)

                # 4. SMS
                if tpl_send_sms and eff_send_sms and (account.use_sms or event_type in courier_events) and account.phone:
                    sms_text = rendered_text
                    if should_send_qr and qr_file_path:
                        import os
                        public_url = f"https://vezuroll.ru/media/img/qr/{os.path.basename(qr_file_path)}"
                        sms_text += f"\n\nСсылка на оплату СБП: {public_url}"
                        
                    logger.info(f"SMS notification triggered for {account.name} ({account.phone}): {sms_text}")
                    log_entry = VkBotMessageLog(
                        account_id=account.id,
                        text=f"[SMS] {sms_text}",
                        event_type=event_type,
                        status=MessageStatus.SENT,
                        sent_at=utc_now()
                    )
                    session.add(log_entry)

            session.commit()

            # Трансляция WebSocket обновления заказа, если менялся статус уведомления курьера
            if order and order.courier_notification_status:
                try:
                    import asyncio
                    from app.api.chat import manager
                    ws_payload = {
                        "type": "courier_status_changed",
                        "order_id": order.id,
                        "order_num": str(order.external_number or order.id),
                        "courier_notification_status": order.courier_notification_status,
                        "courier_name": order.courier_name,
                        "timestamp": int(utc_now().timestamp() * 1000)
                    }
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        loop.create_task(manager.broadcast(ws_payload))
                except Exception as ws_err:
                    logger.debug(f"Failed to broadcast websocket notification: {ws_err}")

    async def send_manual_broadcast(self, text: str, account_ids: List[int] = None, group_ids: List[int] = None, keyboard: Optional[str] = None):
        """
        Ручная рассылка сообщения выбранным аккаунтам или группам.
        """
        with Session(engine) as session:
            recipients = []
            
            if account_ids:
                recipients.extend(session.exec(select(VkBotAccount).where(VkBotAccount.id.in_(account_ids))).all())
            
            if group_ids:
                from app.models.vk_bot import VkBotAccountGroupLink
                stmt = (
                    select(VkBotAccount)
                    .join(VkBotAccountGroupLink)
                    .where(VkBotAccountGroupLink.group_id.in_(group_ids))
                    .where(VkBotAccount.is_active == True)
                )
                recipients.extend(session.exec(stmt).all())

            # Убираем дубликаты по id аккаунта
            unique_recipients = {acc.id: acc for acc in recipients}.values()
            
            from app.core.datetime_utils import utc_now
            tg_token = get_telegram_token(session)

            for account in unique_recipients:
                # VK
                if account.use_vk and account.vk_user_id and account.is_verified:
                    await vk_bot_service.send_message(
                        user_id=account.vk_user_id,
                        message=text,
                        keyboard=keyboard,
                        account_id=account.id,
                        event_type="manual_broadcast"
                    )
                
                # Telegram
                if account.use_tg and account.tg_user_id and account.is_tg_verified:
                    if tg_token:
                        success = await send_telegram_message(account.tg_user_id, text, tg_token)
                        log_entry = VkBotMessageLog(
                            account_id=account.id,
                            text=f"[TG] {text}",
                            event_type="manual_broadcast",
                            status=MessageStatus.SENT if success else MessageStatus.FAILED,
                            error_text=None if success else "Failed to send via Telegram Bot API",
                            sent_at=utc_now() if success else None
                        )
                        session.add(log_entry)

                # MAX
                if account.use_max and (account.max_user_id or account.phone) and account.is_max_verified:
                    target = account.max_user_id or account.phone
                    eff_bot_id = getattr(template, "max_bot_id", None) if template else getattr(account, "max_bot_id", None)
                    eff_mode = (getattr(template, "max_send_mode", None) if template else None) or getattr(account, "max_send_mode", None) or "cascade"
                    success = await send_max_message_helper(
                        target, 
                        text, 
                        session,
                        bot_id=eff_bot_id,
                        prefer_channel=eff_mode
                    )
                    log_entry = VkBotMessageLog(
                        account_id=account.id,
                        text=f"[MAX] {text}",
                        event_type="manual_broadcast",
                        status=MessageStatus.SENT if success else MessageStatus.FAILED,
                        error_text=None if success else "Failed to send via MAX API",
                        sent_at=utc_now() if success else None
                    )
                    session.add(log_entry)

                # SMS
                if account.use_sms and account.phone:
                    logger.info(f"SMS manual broadcast for {account.name} ({account.phone}): {text}")
                    log_entry = VkBotMessageLog(
                        account_id=account.id,
                        text=f"[SMS] {text}",
                        event_type="manual_broadcast",
                        status=MessageStatus.SENT,
                        sent_at=utc_now()
                    )
                    session.add(log_entry)

vk_notification_router = VkNotificationRouter()
