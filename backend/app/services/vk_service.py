import re
import logging
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)
from sqlmodel import Session, select
from app.models.order import Order
from app.models.vk_user import VkUser
from app.models.vk_activity import VkActivity
from app.models.vk_settings import VkSettings
from app.models.customer import Customer
from app.models.vk_message import VkMessage
import httpx
import asyncio
from datetime import datetime
from app.core.datetime_utils import utc_now


def extract_order_id_from_text(text: str, parser_enabled: bool, parser_phrase: str) -> Optional[str]:
    """Извлекает ID заказа из текста сообщения по заданным правилам"""
    if not text:
        return None

    order_number = None

    # 1. Поиск по специфичной фразе (приоритет)
    if parser_enabled:
        # Превращаем шаблон в регулярку: заменяем {order_id} на (\d+)
        regex_pattern = re.escape(parser_phrase).replace(r'\{order_id\}', r'(\d+)')
        match = re.search(regex_pattern, text, re.IGNORECASE)
        if match:
            order_number = match.group(1)

    # 2. Фолбэк на общий поиск номера заказа, если специфичная фраза не найдена
    if not order_number:
        match = re.search(r'(?:заказ|заказа).*?(?:№|#)?\s*(\d+)', text, re.IGNORECASE)
        if match:
            order_number = match.group(1)

    return order_number


async def link_vk_user_to_order(db: Session, vk_id: int, order_number: str, source: str = "parser_realtime") -> bool:
    """Привязывает пользователя VK к клиенту на основе номера заказа"""
    try:
        # Поиск заказа в БД (сначала по ID, потом по внешнему номеру)
        order = db.exec(select(Order).where(Order.id == int(order_number))).first()
        if not order:
            order = db.exec(select(Order).where(Order.external_number == order_number)).first()
        
        if not order:
            return False

        # А. Обновляем/создаем VkUser
        vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
        
        # Получаем доп. данные из VK если есть токен
        vk_settings = db.exec(select(VkSettings)).first()
        bot_token = vk_settings.vk_bot_token if vk_settings else None
        vk_profile = {}
        if bot_token:
            vk_profile = await fetch_vk_user_info(vk_id, bot_token)

        now = utc_now()
        if not vk_user:
            vk_user = VkUser(
                vk_id=vk_id,
                phone=order.customer_phone,
                iiko_customer_id=str(order.customer_id) if order.customer_id else None,
                first_name=vk_profile.get("first_name") or order.customer_name,
                last_name=vk_profile.get("last_name"),
                photo_50=vk_profile.get("photo_50"),
                screen_name=vk_profile.get("domain"),
                is_linked=True,
                linked_at=now,
                linking_source=source,
                last_order_id=order_number
            )
            db.add(vk_user)
        else:
            vk_user.phone = order.customer_phone or vk_user.phone
            vk_user.iiko_customer_id = str(order.customer_id) if order.customer_id else vk_user.iiko_customer_id
            vk_user.first_name = vk_profile.get("first_name") or vk_user.first_name or order.customer_name
            vk_user.last_name = vk_profile.get("last_name") or vk_user.last_name
            vk_user.photo_50 = vk_profile.get("photo_50") or vk_user.photo_50
            vk_user.screen_name = vk_profile.get("domain") or vk_user.screen_name
            vk_user.is_linked = True
            vk_user.linked_at = now
            vk_user.linking_source = source
            vk_user.last_order_id = order_number
            db.add(vk_user)

        # Б. Обновляем профиль Customer (Guest)
        if order.customer_id:
            customer = db.exec(select(Customer).where(Customer.id == order.customer_id)).first()
            if customer:
                customer.vk_user_id = vk_id
                db.add(customer)
        
        db.commit()
        return True
    except Exception as e:
        print(f"Error linking VK user to order {order_number}: {e}")
        db.rollback()
        return False


async def fetch_vk_user_info(vk_id: int, bot_token: str) -> Dict[str, Any]:
    """Получает информацию о пользователе из VK API"""
    url = "https://api.vk.com/method/users.get"
    params = {
        "user_ids": vk_id,
        "fields": "photo_50,domain",
        "access_token": bot_token,
        "v": "5.131"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(url, params=params)
            data = resp.json()
            if "response" in data and len(data["response"]) > 0:
                return data["response"][0]
        except Exception as e:
            print(f"Error fetching VK user info for {vk_id}: {e}")
    return {}


async def process_vk_event(event_data: Dict[str, Any], db: Session, bot_token: str | None):
    event_type = event_data.get("type")
    obj = event_data.get("object", {})

    if event_type == "message_reply" or event_type == "message_new":
        await handle_message(event_type, obj, db, bot_token)
    elif event_type in ["like_add", "wall_reply_new"]:
        await handle_activity(event_type, obj, db, bot_token)


async def handle_message(event_type: str, obj: Dict[str, Any], db: Session, bot_token: str | None):
    # Depending on API version, message might be directly in obj or obj.message
    message = obj if 'text' in obj else obj.get('message', {})
    text = message.get("text", "")
    vk_id = message.get("peer_id") or obj.get("user_id") or message.get("from_id")
    
    if not vk_id or not text:
        return

    # 1. Проверяем настройки парсера
    vk_settings = db.exec(select(VkSettings)).first()
    parser_enabled = vk_settings.vk_parser_enabled if vk_settings else False
    parser_phrase = vk_settings.vk_parser_phrase if vk_settings else "здравствуйте! Ваш заказ {order_id} принят и мы приступили к его приготовлению"
    
    # 1.5. Сохраняем сообщение в историю
    try:
        direction = "outbound" if event_type == "message_reply" else "inbound"
        msg_id = message.get("id") or message.get("conversation_message_id")
        
        # Проверяем не сохраняли ли уже (на случай дублей от вебхуков)
        existing_msg = None
        if msg_id:
            existing_msg = db.exec(
                select(VkMessage).where(VkMessage.vk_message_id == msg_id)
            ).first()
            
        if not existing_msg:
            new_msg = VkMessage(
                vk_message_id=msg_id or 0,
                peer_id=vk_id,
                from_id=message.get("from_id") or vk_id,
                text=text,
                direction=direction,
                payload=obj
            )
            db.add(new_msg)
            db.commit()
    except Exception as e:
        print(f"Error saving VK message to history: {e}")
        db.rollback()

    # 2. Пытаемся извлечь номер заказа (сначала из текущего сообщения, затем из истории)
    order_number = extract_order_id_from_text(text, parser_enabled, parser_phrase)

    # Если в текущем сообщении нет, но есть токен - проверяем историю 10 последних сообщений
    if not order_number and bot_token:
        try:
            url_history = "https://api.vk.com/method/messages.getHistory"
            params_hist = {
                "access_token": bot_token,
                "v": "5.131",
                "peer_id": vk_id,
                "count": 10
            }
            async with httpx.AsyncClient() as client:
                resp_h = await client.get(url_history, params=params_hist)
                data_h = resp_h.json()
                if "response" in data_h:
                    messages = data_h["response"].get("items", [])
                    for msg in messages:
                        hist_text = msg.get("text", "")
                        hist_order_id = extract_order_id_from_text(hist_text, parser_enabled, parser_phrase)
                        if hist_order_id:
                            order_number = hist_order_id
                            break # Нашли самый свежий
        except Exception as e:
            print(f"Error checking VK history for context: {e}")

    if not order_number:
        return

    # 3. Выполняем связку
    # Проверяем, был ли пользователь уже привязан, чтобы не спамить приветствием
    vk_user_before = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    was_linked = vk_user_before.is_linked if vk_user_before else False

    success = await link_vk_user_to_order(db, vk_id, order_number)
            
    # 4. Отправляем уведомление об успешной привязке ТОЛЬКО если это первая привязка
    if success and not was_linked and event_type == "message_new" and bot_token:
        # Получаем имя для приветствия (уже должно быть в заказе или в vk_user)
        vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
        name = vk_user.first_name if vk_user and vk_user.first_name else "гость"
        
        await send_vk_message(
            vk_id=vk_id, 
            message=f"Здравствуйте, {name}! Ваш профиль ВК успешно привязан к вашей карте гостя. Теперь вы будете получать уведомления о заказах здесь.",
            bot_token=bot_token
        )


async def scan_historical_messages(db: Session, bot_token: str, group_id: int, on_progress=None):
    """
    Ретроспективно сканирует историю сообщений группы для привязки пользователей.
    on_progress: callback-функция для отчета о прогрессе
    """
    url_convs = "https://api.vk.com/method/messages.getConversations"
    url_history = "https://api.vk.com/method/messages.getHistory"
    
    vk_settings = db.exec(select(VkSettings)).first()
    parser_enabled = vk_settings.vk_parser_enabled if vk_settings else False
    parser_phrase = vk_settings.vk_parser_phrase if vk_settings else "здравствуйте! Ваш заказ {order_id} принят и мы приступили к его приготовлению"

    total_convs_processed = 0
    total_matches_found = 0
    offset = 0
    count_per_req = 200

    try:
        while True:
            # 1. Получаем список бесед
            params_convs = {
                "access_token": bot_token,
                "v": "5.131",
                "offset": offset,
                "count": count_per_req,
                "extended": 1
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url_convs, params=params_convs)
                data = resp.json()
                
                if "error" in data:
                    print(f"VK API Error (Conversations): {data['error']}")
                    break
                    
                items = data.get("response", {}).get("items", [])
                total_count = data.get("response", {}).get("count", 0)
                
                if not items:
                    break

                for item in items:
                    peer_id = item.get("conversation", {}).get("peer", {}).get("id")
                    if not peer_id:
                        continue

                    # 2. Для каждой беседы сканируем историю
                    hist_offset = 0
                    while True:
                        params_hist = {
                            "access_token": bot_token,
                            "v": "5.131",
                            "peer_id": peer_id,
                            "offset": hist_offset,
                            "count": count_per_req
                        }
                        
                        resp_h = await client.get(url_history, params=params_hist)
                        data_h = resp_h.json()
                        
                        if "error" in data_h:
                            print(f"VK API Error (History {peer_id}): {data_h['error']}")
                            break
                            
                        messages = data_h.get("response", {}).get("items", [])
                        if not messages:
                            break
                            
                        for msg in messages:
                            text = msg.get("text")
                            if not text:
                                continue
                                
                            order_id = extract_order_id_from_text(text, parser_enabled, parser_phrase)
                            if order_id:
                                # Пытаемся привязать
                                if await link_vk_user_to_order(db, peer_id, order_id, source="parser_history"):
                                    total_matches_found += 1
                                
                            # Сохраняем каждое сообщение в общую историю
                            try:
                                msg_id = msg.get("id") or msg.get("conversation_message_id")
                                if msg_id:
                                    existing_msg = db.exec(
                                        select(VkMessage).where(VkMessage.vk_message_id == msg_id)
                                    ).first()
                                    
                                    if not existing_msg:
                                        # Определяем направление
                                        # Если from_id равен peer_id, то это входящее (inbound)
                                        # Если from_id отрицательный и совпадает с group_id (или просто отрицательный), то это исходящее (outbound)
                                        from_id = msg.get("from_id", 0)
                                        direction = "outbound" if from_id < 0 else "inbound"
                                        
                                        new_msg = VkMessage(
                                            vk_message_id=msg_id,
                                            peer_id=peer_id,
                                            from_id=from_id,
                                            text=text,
                                            direction=direction,
                                            payload=msg,
                                            created_at=datetime.fromtimestamp(msg.get("date", utc_now().timestamp()))
                                        )
                                        db.add(new_msg)
                            except Exception as e:
                                print(f"Error saving historical message {msg_id}: {e}")
                        
                        db.commit() # Коммитим пачку сообщений из истории одного диалога
                        
                        hist_offset += count_per_req
                        if len(messages) < count_per_req:
                            break
                        
                        # Небольшая пауза чтобы не словить Rate Limit
                        await asyncio.sleep(0.1)

                    total_convs_processed += 1
                    
                    if on_progress:
                        await on_progress(total_convs_processed, total_count, total_matches_found)

                offset += count_per_req
                if offset >= total_count:
                    break
                    
        return {
            "conversations_processed": total_convs_processed,
            "matches_found": total_matches_found,
            "completed_at": utc_now()
        }
    except Exception as e:
        print(f"Error during historical scan: {e}")
        return {"error": str(e), "conversations_processed": total_convs_processed}


async def handle_activity(event_type: str, obj: Dict[str, Any], db: Session, bot_token: str | None):
    # Example logic for activity points
    vk_id = obj.get("liker_id") or obj.get("from_id")
    if not vk_id:
        return
        
    item_id = str(obj.get("item_id") or obj.get("post_id") or obj.get("id"))
    
    # Check if user is linked
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    
    if not vk_user or not vk_user.is_linked:
        return
        
    # Check if action already recorded
    existing_action = db.exec(
        select(VkActivity)
        .where(VkActivity.vk_id == vk_id)
        .where(VkActivity.action_type == event_type)
        .where(VkActivity.item_id == item_id)
    ).first()
    
    if existing_action:
        return
        
    # Award points
    points = 5 if event_type == "like_add" else 10
    
    activity = VkActivity(
        vk_id=vk_id,
        action_type=event_type,
        item_id=item_id,
        points=points,
        is_synced=False
    )
    db.add(activity)
    
    vk_user.vk_bonus_balance += points
    db.add(vk_user)
    
    db.commit()
    
    # Send notification
    if bot_token:
        await send_vk_message(
            vk_id=vk_id,
            message=f"Вам начислено {points} баллов за активность! Ваш локальный рейтинг: {vk_user.vk_bonus_balance} руб.",
            bot_token=bot_token
        )


async def send_vk_message(vk_id: int, message: str, bot_token: str | None = None):
    if not bot_token:
        print("VK_BOT_TOKEN is not configured")
        return False
        
    url = "https://api.vk.com/method/messages.send"
    import random
    
    params = {
        "user_id": vk_id,
        "message": message,
        "random_id": random.randint(1, 2147483647),
        "access_token": bot_token,
        "v": "5.131"
    }
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=params)
            data = response.json()
            if "error" in data:
                print(f"VK API Error: {data['error']}")
                return False
            return True
        except Exception as e:
            print(f"Failed to send VK message: {e}")
            return False


async def send_guest_order_notification(db: Session, order: Order, event_type: str):
    """
    Отправляет уведомление гостю в ВК об изменении статуса заказа.
    Использует данные заказа из админки и шаблоны из настроек.
    """
    try:
        # 1. Получаем настройки ВК
        vk_settings = db.exec(select(VkSettings)).first()
        if not vk_settings or not vk_settings.vk_notification_settings:
            return

        settings = vk_settings.vk_notification_settings
        bot_token = vk_settings.vk_bot_token
        if not bot_token:
            return

        # 2. Ищем привязанного пользователя ВК
        # Сначала по vk_user_id в клиенте, если есть
        vk_id = None
        if order.customer_id:
            customer = db.exec(select(Customer).where(Customer.id == order.customer_id)).first()
            if customer and customer.vk_user_id:
                vk_id = customer.vk_user_id
        
        # Если не нашли в клиенте, ищем в VkUser по телефону
        if not vk_id and order.customer_phone:
            vk_user = db.exec(select(VkUser).where(VkUser.phone == order.customer_phone)).first()
            if vk_user and vk_user.is_linked:
                vk_id = vk_user.vk_id

        if not vk_id:
            return

        # 3. Определяем категорию настроек (delivery или pickup)
        order_type_key = "delivery" if order.order_type == "Доставка" else "pickup"
        type_settings = settings.get(order_type_key, {})
        
        if not type_settings.get("enabled"):
            return

        # 4. Маппинг статуса заказа на ключ в настройках
        from app.models.order import OrderStatus
        status_map = {
            OrderStatus.confirmed: "confirmed",
            OrderStatus.cooking: "cooking",
            OrderStatus.ready: "ready",
            OrderStatus.ready_for_pickup: "ready", # Для самовывоза используем 'ready'
            OrderStatus.delivering: "delivering",
            OrderStatus.delivered: "delivered",
            OrderStatus.closed: "delivered", # Закрыт приравниваем к доставлен
            OrderStatus.cancelled: "cancelled"
        }
        
        status_key = status_map.get(order.status)
        if not status_key:
            return

        status_config = type_settings.get("statuses", {}).get(status_key, {})
        if not status_config.get("enabled") or not status_config.get("template"):
            return

        template = status_config["template"]

        # 5. Формируем переменные для шаблона
        # Состав заказа
        items_text = ""
        if order.order_items_details:
            items_list = []
            for item in order.order_items_details:
                name = item.get("name", "Товар")
                amount = item.get("amount", 1)
                items_list.append(f"- {name} x{amount}")
            items_text = "\n".join(items_list)

        # Статус текстом
        status_names = {
            OrderStatus.confirmed: "Подтвержден",
            OrderStatus.cooking: "Готовится",
            OrderStatus.ready: "Готов",
            OrderStatus.ready_for_pickup: "Готов к выдаче",
            OrderStatus.delivering: "В пути",
            OrderStatus.delivered: "Доставлен",
            OrderStatus.closed: "Завершен",
            OrderStatus.cancelled: "Отменен"
        }

        variables = {
            "{order_number}": order.external_number or str(order.id),
            "{order_type}": order.order_type or "Заказ",
            "{address}": order.delivery_address or "---",
            "{customer_name}": order.customer_name or "Гость",
            "{items}": items_text,
            "{total_sum}": f"{float(order.total_with_discount or 0):.0f}",
            "{status}": status_names.get(order.status, "Обработан")
        }

        # 6. Заменяем переменные в шаблоне
        message = template
        for var, value in variables.items():
            message = message.replace(var, str(value))

        # 7. Отправляем сообщение
        await send_vk_message(vk_id=vk_id, message=message, bot_token=bot_token)
        logger.info(f"Sent VK notification to guest {vk_id} for order {order.id} (Status: {order.status})")

    except Exception as e:
        logger.error(f"Error sending guest VK notification: {e}")
