import re
import logging
from typing import Dict, Any, Optional, List, Tuple

logger = logging.getLogger(__name__)
from sqlmodel import Session, select
from app.models.order import Order
from app.models.vk_user import VkUser
from app.models.vk_activity import VkActivity
from app.models.vk_settings import VkSettings
from app.models.customer import Customer
from app.models.vk_message import VkMessage
from app.models.vk_bot_connection import VkBotConnection
from app.models.vk_cover_bot import VkCoverBot
from app.models.bot_command import BotCommand, BotUserState
from app.models.review import OrderReview
import httpx
import asyncio
from datetime import datetime
from app.core.datetime_utils import utc_now


def extract_order_id_from_text(text: str, parser_enabled: bool, parser_phrase: str, parser_mask: Optional[str] = None) -> Optional[str]:
    """Извлекает ID заказа из текста сообщения по заданным правилам и валидирует по маске"""
    if not text or not parser_enabled or not parser_phrase:
        return None

    def check_mask(order_id: str, mask: Optional[str]) -> bool:
        if not mask or mask.strip() in ("", "*"):
            return True
        parts = []
        for char in mask.strip():
            if char == '*':
                parts.append('.')
            else:
                parts.append(re.escape(char))
        pattern = "^" + "".join(parts) + "$"
        return bool(re.match(pattern, order_id))

    # Нормализуем фразу, очищая от начальных/конечных пробелов
    phrase_clean = parser_phrase.strip()

    # Превращаем шаблон в регулярку: заменяем {order_id} на (\S+) для поддержки комбинированных номеров
    # Ищем фразу как подстроку (без ^ и $), используя re.search
    regex_pattern = re.escape(phrase_clean).replace(r'\{order_id\}', r'(\S+)')
    match = re.search(regex_pattern, text, re.IGNORECASE)
    if match:
        candidate = match.group(1)
        # Очистим кандидата от знаков препинания на конце, если они захватились
        candidate = candidate.rstrip('.,!?;:)')
        if check_mask(candidate, parser_mask):
            return candidate

    return None


def is_ignored_vk_id(vk_id: int, ignored_ids_str: Optional[str]) -> bool:
    """Проверяет, входит ли VK ID в список игнорируемых ID"""
    if not ignored_ids_str:
        return False
    try:
        ignored_ids = [int(x.strip()) for x in ignored_ids_str.split(",") if x.strip().isdigit()]
        return vk_id in ignored_ids
    except Exception as e:
        logger.error(f"Error parsing vk_parser_ignored_ids: {e}")
        return False


async def link_vk_user_to_order(db: Session, vk_id: int, order_number: str, source: str = "parser_realtime", group_id: Optional[int] = None) -> bool:
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
        bot_token = None
        if group_id:
            bot = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id, VkBotConnection.is_active == True)).first()
            if bot:
                bot_token = bot.vk_bot_token
        
        if not bot_token:
            vk_settings = db.exec(select(VkSettings)).first()
            bot_token = vk_settings.vk_bot_token if vk_settings else None
            
        vk_profile = {}
        if bot_token:
            vk_profile = await fetch_vk_user_info(vk_id, bot_token)

        now = utc_now()
        if not vk_user:
            vk_user = VkUser(
                vk_id=vk_id,
                vk_group_id=group_id,
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
            vk_user.vk_group_id = group_id or vk_user.vk_group_id
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
    url = "https://api.vk.ru/method/users.get"
    params = {
        "user_ids": vk_id,
        "fields": "photo_50,domain",
        "access_token": bot_token,
        "v": "5.199"
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


async def handle_lead_form_event(obj: Dict[str, Any], db: Session, bot_token: str | None, group_id: Optional[int] = None):
    """Обработчик события новой лид-формы ВКонтакте (lead_forms_new)"""
    vk_id = obj.get("user_id")
    answers = obj.get("answers", [])
    
    if not vk_id or not answers:
        return
        
    phone = None
    for ans in answers:
        if ans.get("key") == "phone" or "телефон" in str(ans.get("question", "")).lower():
            phone = ans.get("answer")
            break
            
    if not phone:
        return
        
    try:
        points = await link_phone_to_vk_user(db, vk_id, phone, bot_token, group_id, source="lead_form")
        
        # Удаляем FSM состояние
        from app.models.bot_command import BotUserState
        user_state = db.exec(
            select(BotUserState)
            .where(BotUserState.messenger == "vk")
            .where(BotUserState.peer_id == str(vk_id))
        ).first()
        if user_state:
            db.delete(user_state)
            db.commit()
            
        if bot_token:
            await send_vk_message(
                vk_id=vk_id,
                message=f"Проверка номера телефона через форму сбора заявок успешно пройдена! Ваш бонусный баланс: {int(points)} бонусов.",
                bot_token=bot_token
            )
    except Exception as e:
        logger.error(f"Error handling lead form event: {e}")


async def run_first_comment_in_background(obj: Dict[str, Any], bot_token: str | None, group_id: Optional[int]):
    from app.core.database import Session, engine
    from app.services.vk_first_comment_service import vk_first_comment_service
    with Session(engine) as session:
        try:
            await vk_first_comment_service.process_new_post(session, obj, bot_token, group_id)
        except Exception as e:
            logger.error(f"Error in background vk_first_comment_service.process_new_post: {e}", exc_info=True)


async def handle_courier_social_feedback(
    channel: str, 
    user_id: Any, 
    feedback_type: str, 
    feedback_text: Optional[str], 
    db: Session
):
    """
    Обработка обратной связи от курьера в соцсетях (VK, Telegram, MAX):
    - feedback_type == 'read': курьер прочитал уведомление -> желтый кружок 🟡
    - feedback_type in ('reaction', 'reply'): курьер поставил реакцию или ответил -> зеленый кружок 🟢
    """
    if not user_id:
        return
    try:
        from app.models.vk_bot import VkBotAccount, CourierOrderNotification
        from app.models.order import Order
        from app.core.datetime_utils import utc_now
        from app.api.chat import manager
        import asyncio

        uid_str = str(user_id).strip()
        acc = None
        if channel == "vk":
            if uid_str.isdigit():
                acc = db.exec(select(VkBotAccount).where(VkBotAccount.vk_user_id == int(uid_str))).first()
        elif channel == "tg":
            if uid_str.isdigit():
                acc = db.exec(select(VkBotAccount).where(VkBotAccount.tg_user_id == int(uid_str))).first()
        elif channel == "max":
            acc = db.exec(select(VkBotAccount).where((VkBotAccount.max_user_id == uid_str) | (VkBotAccount.phone == uid_str))).first()

        if not acc or not getattr(acc, "is_courier", False):
            return

        latest_notif = db.exec(
            select(CourierOrderNotification)
            .where(CourierOrderNotification.account_id == acc.id)
            .order_by(CourierOrderNotification.id.desc())
        ).first()

        target_order = None
        if latest_notif:
            target_order = db.get(Order, latest_notif.order_id)

        if not target_order:
            courier_names = [acc.name]
            if acc.employee_id:
                from app.models.employee import Employee
                emp = db.get(Employee, acc.employee_id)
                if emp and emp.name:
                    courier_names.append(emp.name)
            target_order = db.exec(
                select(Order)
                .where(Order.order_type == "Доставка")
                .where(Order.courier_name.in_(courier_names))
                .where(Order.status.in_(["new", "confirmed", "preparing", "cooking", "ready", "delivering", "ready_for_pickup"]))
                .order_by(Order.id.desc())
            ).first()

        if not target_order:
            return

        now = utc_now()
        changed = False

        if feedback_type == "read":
            if target_order.courier_notification_status == "unread":
                target_order.courier_notification_status = "read"
                target_order.courier_read_at = now
                db.add(target_order)
                changed = True
                if latest_notif and latest_notif.status == "unread":
                    latest_notif.status = "read"
                    latest_notif.read_at = now
                    db.add(latest_notif)

        elif feedback_type in ("reaction", "reply"):
            target_order.courier_notification_status = "accepted"
            target_order.courier_accepted_at = now
            target_order.courier_accepted_source = f"{channel}_{feedback_type}"
            target_order.courier_last_message_text = feedback_text or ("Реакция курьера" if feedback_type == "reaction" else "Ответ курьера")
            db.add(target_order)
            changed = True
            if latest_notif:
                latest_notif.status = "accepted"
                latest_notif.accepted_at = now
                if feedback_type == "reaction":
                    latest_notif.reaction = feedback_text
                else:
                    latest_notif.reply_text = feedback_text
                db.add(latest_notif)

        if changed:
            db.commit()
            db.refresh(target_order)
            try:
                ws_payload = {
                    "type": "courier_status_changed",
                    "order_id": target_order.id,
                    "order_num": str(target_order.external_number or target_order.id),
                    "courier_notification_status": target_order.courier_notification_status,
                    "courier_name": target_order.courier_name,
                    "timestamp": int(now.timestamp() * 1000)
                }
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(manager.broadcast(ws_payload))
            except Exception as ws_e:
                logger.debug(f"Failed to broadcast WS for courier feedback: {ws_e}")
    except Exception as err:
        logger.error(f"Error handling courier social feedback: {err}")


async def process_vk_event(event_data: Dict[str, Any], db: Session, bot_token: str | None, group_id: Optional[int] = None):
    event_type = event_data.get("type")
    obj = event_data.get("object", {})

    if event_type == "message_reply" or event_type == "message_new":
        await handle_message(event_type, obj, db, bot_token, group_id)
    elif event_type == "message_event":
        vk_uid = obj.get("user_id")
        if vk_uid:
            await handle_courier_social_feedback("vk", vk_uid, "reaction", "Кнопка в сообщении", db)
        await handle_message_event(obj, db, bot_token, group_id)
    elif event_type in ["message_read", "messages_read"]:
        vk_uid = obj.get("user_id") or obj.get("peer_id")
        if vk_uid:
            await handle_courier_social_feedback("vk", vk_uid, "read", None, db)
    elif event_type in ["message_reaction_event", "message_reaction"]:
        vk_uid = obj.get("user_id") or obj.get("peer_id")
        reaction_val = obj.get("reaction_id") or obj.get("payload") or "👍"
        if vk_uid:
            await handle_courier_social_feedback("vk", vk_uid, "reaction", str(reaction_val), db)
    elif event_type == "lead_forms_new":
        await handle_lead_form_event(obj, db, bot_token, group_id)
    elif event_type in ["like_add", "like_remove", "wall_reply_new", "wall_reply_delete", "wall_repost", "poll_vote_new", "group_join", "group_leave"]:
        if event_type == "wall_reply_new" and bot_token:
            try:
                from app.services.vk_contest_service import vk_contest_service
                await vk_contest_service.process_contest_move(db, obj, bot_token, group_id)
            except Exception as e:
                logger.error(f"Error in vk_contest_service.process_contest_move: {e}", exc_info=True)
        try:
            from app.services.vk_activity_service import vk_activity_service
            await vk_activity_service.process_activity_event(db, event_type, obj, bot_token, group_id)
        except Exception as e:
            logger.error(f"Error in vk_activity_service.process_activity_event: {e}", exc_info=True)
    elif event_type == "wall_post_new":
        # Запускаем в фоновой задаче, чтобы вернуть 'ok' Callback API без задержки
        import asyncio
        asyncio.create_task(run_first_comment_in_background(obj, bot_token, group_id))
    elif event_type in ["message_allow", "message_deny"]:
        await handle_subscription_event(event_type, obj, db, group_id)

    if group_id:
        try:
            conn = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == group_id, VkBotConnection.is_active == True)).first()
            if conn:
                bot = db.exec(
                    select(VkCoverBot)
                    .where(VkCoverBot.vk_bot_connection_id == conn.id)
                    .where(VkCoverBot.is_active == True)
                    .where(VkCoverBot.update_interval == "callback")
                ).first()
                if bot:
                    from app.services.vk_cover_service import vk_cover_service
                    asyncio.create_task(vk_cover_service.publish_cover(db, bot))
        except Exception as e:
            logger.error(f"Error checking reactive cover update: {e}")


async def handle_subscription_event(event_type: str, obj: Dict[str, Any], db: Session, group_id: Optional[int] = None):
    vk_id = obj.get("user_id")
    if not vk_id:
        return
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    if vk_user:
        vk_user.is_subscribed = (event_type == "message_allow")
        if group_id:
            vk_user.vk_group_id = group_id
        db.add(vk_user)
        db.commit()
        logger.info(f"VK User {vk_id} subscription status updated to: {vk_user.is_subscribed}")
    elif event_type == "message_allow":
        vk_user = VkUser(
            vk_id=vk_id,
            is_subscribed=True,
            vk_group_id=group_id
        )
        db.add(vk_user)
        db.commit()
        logger.info(f"VK User {vk_id} created on subscription allow event")


async def auto_link_vk_user_from_customer(db: Session, vk_id: int):
    """
    Автоматически привязывает аккаунт ВКонтакте, если в админке
    данный vk_id уже привязан к какому-либо Customer.
    """
    try:
        from app.models.vk_user import VkUser
        from app.models.customer import Customer
        from app.models.vk_activity_settings import VkActivitySettings
        from app.services.vk_activity_service import vk_activity_service
        
        # Находим пользователя
        vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
        if not vk_user:
            # Создаем VkUser, если его нет в БД
            vk_user = VkUser(
                vk_id=vk_id,
                is_linked=False,
                vk_bonus_balance=0,
                vk_bonus_balance_synced=0
            )
            db.add(vk_user)
            db.commit()
            db.refresh(vk_user)
            
        if not vk_user.is_linked:
            # Ищем клиента с этим vk_user_id
            customer = db.exec(select(Customer).where(Customer.vk_user_id == vk_id)).first()
            if customer and customer.phone:
                # Нашли связку в админке!
                vk_user.phone = customer.phone
                vk_user.iiko_customer_id = customer.iiko_customer_id
                vk_user.is_linked = True
                vk_user.linking_source = "auto_parser_link"
                vk_user.linked_at = utc_now()
                db.add(vk_user)
                db.commit()
                db.refresh(vk_user)
                
                logger.info(f"Auto-linked VkUser {vk_id} to Customer {customer.phone} based on admin relation")
                
                # Запускаем синхронизацию баллов активности с iikoCard
                settings = None
                if vk_user.vk_group_id:
                    settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == vk_user.vk_group_id)).first()
                if not settings:
                    settings = db.exec(select(VkActivitySettings)).first()
                    
                # Авто-синхронизация при привязке отключена
                # if settings and settings.sync_with_iiko and getattr(settings, "sync_on_verification", True):
                #     await vk_activity_service.sync_vk_user_points_to_iiko(db, vk_user, settings)
    except Exception as e:
        logger.error(f"Error in auto_link_vk_user_from_customer for VK ID {vk_id}: {e}")
        try:
            db.rollback()
        except Exception:
            pass


async def handle_message(event_type: str, obj: Dict[str, Any], db: Session, bot_token: str | None, group_id: Optional[int] = None):
    # Depending on API version, message might be directly in obj or obj.message
    message = obj if 'text' in obj else obj.get('message', {})
    text = message.get("text", "")
    vk_id = message.get("peer_id") or obj.get("user_id") or message.get("from_id")
    
    if not vk_id:
        return

    # Обработка ответа курьера (перевод кружка в зеленый при ответе)
    if event_type == "message_new" and vk_id:
        await handle_courier_social_feedback("vk", vk_id, "reply", text, db)

    # Проверяем наличие payload (например, нажатие обычной inline кнопки с payload)
    payload_str = message.get("payload")
    if payload_str:
        try:
            import json
            payload = json.loads(payload_str)
            if isinstance(payload, dict) and payload.get("action") == "rate_order":
                await handle_rate_order_payload(vk_id, payload, db, bot_token, group_id)
                return
        except Exception as e:
            logger.error(f"Error parsing VK button payload in handle_message: {e}")

    if not text:
        attachments = message.get("attachments") or []
        if attachments:
            type_names = {
                "photo": "Фотография",
                "sticker": "Стикер",
                "audio_message": "Голосовое сообщение",
                "video": "Видеозапись",
                "doc": "Документ",
                "audio": "Аудиозапись",
                "wall": "Запись со стены",
                "market": "Товар",
                "poll": "Опрос"
            }
            types = [type_names.get(att.get("type"), att.get("type", "Вложение")) for att in attachments]
            text = f"[{', '.join(types)}]"
        elif message.get("geo"):
            text = "[Местоположение]"
        elif message.get("fwd_messages"):
            text = "[Пересланные сообщения]"
        else:
            return

    # 1. Проверяем настройки парсера
    vk_settings = db.exec(select(VkSettings)).first()
    parser_enabled = vk_settings.vk_parser_enabled if vk_settings else False
    parser_phrase = vk_settings.vk_parser_phrase if vk_settings else "здравствуйте! Ваш заказ {order_id} принят и мы приступили к его приготовлению"
    parser_mask = vk_settings.vk_parser_mask if vk_settings else None
    
    ignored_ids_str = vk_settings.vk_parser_ignored_ids if vk_settings else None
    
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
                payload=obj,
                vk_group_id=group_id
            )
            db.add(new_msg)
            db.commit()

            # Также пишем в мультичат
            try:
                from app.models.chat import MultichatMessage
                
                vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
                peer_name = None
                peer_avatar = None
                if vk_user:
                    if vk_user.first_name or vk_user.last_name:
                        peer_name = f"{vk_user.first_name or ''} {vk_user.last_name or ''}".strip()
                    peer_avatar = vk_user.photo_50
                
                if not peer_name:
                    from app.models.customer import Customer
                    cust = db.exec(select(Customer).where(Customer.vk_user_id == vk_id)).first()
                    if cust:
                        c_name = f"{cust.first_name or cust.name or ''} {cust.last_name or cust.surname or ''}".strip()
                        if c_name:
                            peer_name = c_name

                if not peer_name and direction == "inbound":
                    try:
                        vk_profile = await fetch_vk_user_info(vk_id, bot_token) if bot_token else {}
                        if vk_profile:
                            peer_name = f"{vk_profile.get('first_name', '')} {vk_profile.get('last_name', '')}".strip()
                            peer_avatar = vk_profile.get("photo_50")
                            # Сохраняем в VkUser для будущих сообщений
                            if vk_user:
                                vk_user.first_name = vk_profile.get("first_name") or vk_user.first_name
                                vk_user.last_name = vk_profile.get("last_name") or vk_user.last_name
                                vk_user.photo_50 = peer_avatar or vk_user.photo_50
                                vk_user.screen_name = vk_profile.get("domain") or vk_user.screen_name
                                db.add(vk_user)
                                db.commit()
                    except Exception:
                        pass
                
                if not peer_name:
                    peer_name = f"Пользователь VK {vk_id}"

                multichat_msg = MultichatMessage(
                    channel="vk",
                    channel_id=str(group_id) if group_id else None,
                    peer_id=str(vk_id),
                    peer_name=peer_name,
                    peer_avatar=peer_avatar,
                    from_id=str(message.get("from_id") or vk_id),
                    text=text,
                    direction=direction,
                    external_id=str(msg_id) if msg_id else None,
                    is_read=False if direction == "inbound" else True,
                    payload=obj
                )
                db.add(multichat_msg)
                db.commit()

                # Логирование в Центр уведомлений
                if direction == "inbound":
                    try:
                        import time
                        from app.api.notifications import log_system_notification
                        log_system_notification(
                            db=db,
                            title=f"Сообщение ВК от {peer_name}",
                            subtitle=f"Сообщество ВК • ID: {vk_id}",
                            body=text or "[Медиа/Вложение]",
                            event_type="vk_message",
                            category="vk_message",
                            url="/multichat",
                            badge_text="ВКонтакте",
                            badge_color="primary",
                            external_key=f"vk_msg_{msg_id or int(time.time())}"
                        )
                    except Exception as vk_feed_err:
                        logger.warning(f"Error logging VK feed notification: {vk_feed_err}")
                
                # Трансляция по вебсокетам и мгновенная инвалидация кэша диалогов
                try:
                    from app.api.multichat import broadcast_ws_message
                    await broadcast_ws_message(multichat_msg)
                except Exception as ws_ex:
                    logger.debug(f"WS broadcast error in vk_service: {ws_ex}")
            except Exception as multichat_err:
                print(f"Error saving VK message to multichat: {multichat_err}")
                db.rollback()
    except Exception as e:
        print(f"Error saving VK message to history: {e}")
        db.rollback()

    # 1.6. Обработка команд ботов и FSM (только для входящих сообщений)
    if direction == "inbound":
        # Проверяем авто-привязку из админки/парсера
        await auto_link_vk_user_from_customer(db, vk_id)
        
        parsed_payload = None
        payload_str = message.get("payload")
        if payload_str:
            try:
                import json
                parsed_payload = json.loads(payload_str)
            except:
                pass
        fsm_processed = await handle_bot_commands_and_fsm(vk_id, text, db, bot_token, group_id, payload=parsed_payload)
        if fsm_processed:
            return

    # 2. Пытаемся извлечь номер заказа (сначала из текущего сообщения, затем из истории)
    # Пропускаем парсинг, если отправитель находится в списке игнорируемых ID (например, менеджер/администратор)
    order_number = None
    if vk_id and is_ignored_vk_id(vk_id, ignored_ids_str):
        logger.info(f"VK ID {vk_id} is in ignored list, skipping order parsing.")
    else:
        order_number = extract_order_id_from_text(text, parser_enabled, parser_phrase, parser_mask)

    # Если в текущем сообщении нет, но есть токен - проверяем историю 10 последних сообщений
    if not order_number and bot_token and not (vk_id and is_ignored_vk_id(vk_id, ignored_ids_str)):
        try:
            url_history = "https://api.vk.ru/method/messages.getHistory"
            params_hist = {
                "access_token": bot_token,
                "v": "5.199",
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
                        hist_order_id = extract_order_id_from_text(hist_text, parser_enabled, parser_phrase, parser_mask)
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

    success = await link_vk_user_to_order(db, vk_id, order_number, group_id=group_id)
            
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
    url_convs = "https://api.vk.ru/method/messages.getConversations"
    url_history = "https://api.vk.ru/method/messages.getHistory"
    
    vk_settings = db.exec(select(VkSettings)).first()
    parser_enabled = vk_settings.vk_parser_enabled if vk_settings else False
    parser_phrase = vk_settings.vk_parser_phrase if vk_settings else "здравствуйте! Ваш заказ {order_id} принят и мы приступили к его приготовлению"
    parser_mask = vk_settings.vk_parser_mask if vk_settings else None
    ignored_ids_str = vk_settings.vk_parser_ignored_ids if vk_settings else None

    total_convs_processed = 0
    total_matches_found = 0
    offset = 0
    count_per_req = 200

    try:
        while True:
            # 1. Получаем список бесед
            params_convs = {
                "access_token": bot_token,
                "v": "5.199",
                "offset": offset,
                "count": count_per_req,
                "extended": 1
            }
            
            async with httpx.AsyncClient() as client:
                resp = await client.get(url_convs, params=params_convs)
                data = resp.json()
                
                if "error" in data:
                    error_data = data.get("error", {})
                    if error_data.get("error_code") == 901:
                        # User blocked group messages
                        logger.warning(f"Error 901: User {peer_id} denied messages from group. Marking is_subscribed = False")
                        try:
                            stmt_u = select(VkUser).where(VkUser.vk_id == peer_id)
                            u = db.exec(stmt_u).first() if 'db' in locals() and db else None
                            if u:
                                u.is_subscribed = False
                                db.add(u)
                                db.commit()
                        except Exception:
                            pass

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
                    if peer_id and is_ignored_vk_id(peer_id, ignored_ids_str):
                        continue

                    # 2. Для каждой беседы сканируем историю
                    hist_offset = 0
                    while True:
                        params_hist = {
                            "access_token": bot_token,
                            "v": "5.199",
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
                            
                            from_id = msg.get("from_id", 0)
                            if from_id and is_ignored_vk_id(from_id, ignored_ids_str):
                                continue
                                
                            order_id = extract_order_id_from_text(text, parser_enabled, parser_phrase, parser_mask)
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


async def handle_activity(event_type: str, obj: Dict[str, Any], db: Session, bot_token: str | None, group_id: Optional[int] = None):
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


async def upload_vk_photo_detailed(bot_token: str, image_path: str, peer_id: int) -> Tuple[Optional[str], Optional[str]]:
    """
    Загружает изображение (локальный путь или URL) на сервера VK.
    Возвращает кортеж (attachment, effective_bot_token).
    effective_bot_token — токен, который фактически загрузил и сохранил фото на сервере VK.
    Именно этот токен ДОЛЖЕН использоваться для messages.send, иначе VK вырежет вложение!
    """
    import os
    import httpx
    import tempfile
    import requests
    import asyncio
    
    temp_file = None
    try:
        # Если это URL, скачиваем во временный файл
        if image_path.startswith("http://") or image_path.startswith("https://"):
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(image_path)
                if resp.status_code == 200:
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".jpg")
                    temp_file.write(resp.content)
                    temp_file.close()
                    image_path = temp_file.name
                else:
                    return None, None

        if not os.path.exists(image_path):
            return None, None

        effective_token = bot_token
        # 1. Получаем upload_url
        url = "https://api.vk.com/method/photos.getMessagesUploadServer"
        params = {"access_token": effective_token, "v": "5.199"}
        if peer_id:
            params["peer_id"] = peer_id
            
        async with httpx.AsyncClient(timeout=25.0) as client:
            res = await client.get(url, params=params)
            data = res.json()

            # Если нет прав photos у переданного bot_token (ошибка 15 / subcode 1133), 
            # или ошибка 901 (нет прав писать пользователю у этого токена), 
            # пробуем резервный токен основного сообщества БЕЗ peer_id:
            if "error" in data or "response" not in data:
                from app.core.database import engine
                from sqlmodel import Session, select
                from app.models.vk_bot_connection import VkBotConnection
                from app.models.vk_settings import VkSettings
                fallback_token = None
                with Session(engine) as db_sess:
                    main_bot = db_sess.exec(select(VkBotConnection).where(VkBotConnection.is_main == True, VkBotConnection.is_active == True)).first()
                    if main_bot and main_bot.vk_bot_token and main_bot.vk_bot_token != effective_token:
                        fallback_token = main_bot.vk_bot_token
                    if not fallback_token:
                        vk_settings = db_sess.exec(select(VkSettings)).first()
                        if vk_settings and vk_settings.vk_bot_token and vk_settings.vk_bot_token != effective_token:
                            fallback_token = vk_settings.vk_bot_token
                if fallback_token:
                    effective_token = fallback_token
                    # Для резервного токена вызываем БЕЗ peer_id, чтобы не требовать разрешений пользователя для чужой группы
                    res = await client.get(url, params={"access_token": effective_token, "v": "5.199"})
                    data = res.json()

            if "response" not in data:
                print(f"Error getting VK upload server: {data.get('error')}")
                return None, None
            upload_url = data["response"]["upload_url"]

            # 2. Загружаем файл через requests в отдельном потоке (работает моментально без таймаутов)
            file_name = os.path.basename(image_path) or "image.png"
            mime_type = "image/png" if file_name.lower().endswith(".png") else "image/jpeg"
            
            def _do_upload():
                with open(image_path, "rb") as f:
                    content_bytes = f.read()
                    r = requests.post(upload_url, files={"photo": (file_name, content_bytes, mime_type)}, timeout=25.0)
                    return r.json()

            upload_data = await asyncio.to_thread(_do_upload)

            if not upload_data or "photo" not in upload_data or not upload_data["photo"] or upload_data["photo"] == "[]":
                print(f"VK upload server returned empty photo: {upload_data}")
                return None, None

            # 3. Сохраняем фото под effective_token
            save_url = "https://api.vk.com/method/photos.saveMessagesPhoto"
            save_params = {
                "access_token": effective_token,
                "v": "5.199",
                "photo": upload_data["photo"],
                "server": upload_data["server"],
                "hash": upload_data["hash"]
            }
            res_save = await client.post(save_url, data=save_params, timeout=25.0)
            save_data = res_save.json()
            
            if "response" not in save_data or len(save_data["response"]) == 0:
                print(f"Error saving VK message photo: {save_data.get('error')}")
                return None, None
            
            photo_info = save_data["response"][0]
            attachment = f"photo{photo_info['owner_id']}_{photo_info['id']}"
            return attachment, effective_token
            
    except Exception as e:
        print(f"Error uploading VK photo: {e}")
        return None, None
    finally:
        if temp_file:
            try:
                os.unlink(temp_file.name)
            except:
                pass

async def upload_vk_photo(bot_token: str, image_path: str, peer_id: int) -> Optional[str]:
    """
    Загружает изображение (локальный путь или URL) на сервера VK и возвращает attachment.
    """
    att, _ = await upload_vk_photo_detailed(bot_token, image_path, peer_id)
    return att

async def send_vk_message(
    vk_id: int, 
    message: str, 
    bot_token: str | None = None,
    image_path: str | None = None,
    keyboard: str | dict | list | None = None
):
    if not bot_token:
        print("VK_BOT_TOKEN is not configured")
        return False
        
    url = "https://api.vk.com/method/messages.send"
    import random
    import json
    
    params = {
        "user_id": vk_id,
        "message": message,
        "random_id": random.randint(1, 2147483647),
        "access_token": bot_token,
        "v": "5.199"
    }
    
    # 1. Обработка картинки
    if image_path:
        attachment, effective_token = await upload_vk_photo_detailed(bot_token, image_path, vk_id)
        if attachment:
            params["attachment"] = attachment
            if effective_token:
                params["access_token"] = effective_token
            
    # 2. Обработка клавиатуры
    if keyboard:
        if isinstance(keyboard, (dict, list)):
            params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
        elif isinstance(keyboard, str) and keyboard.strip():
            params["keyboard"] = keyboard
            
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, data=params)
            data = response.json()
            if "error" in data:
                print(f"VK API Error: {data['error']}")
                return False
            # Возвращаем message_id (response - это ID отправленного сообщения)
            return data.get("response") or True
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

        # 2. Ищем привязанного пользователя ВК
        vk_user = None
        if order.customer_id:
            customer = db.exec(select(Customer).where(Customer.id == order.customer_id)).first()
            if customer and customer.vk_user_id:
                vk_user = db.exec(select(VkUser).where(VkUser.vk_id == customer.vk_user_id)).first()
        
        # Если не нашли в клиенте, ищем в VkUser по телефону
        if not vk_user and order.customer_phone:
            vk_user = db.exec(select(VkUser).where(VkUser.phone == order.customer_phone)).first()

        if not vk_user or not vk_user.is_linked:
            return

        # Проверяем разрешения и блокировки
        if vk_user.is_blocked:
            logger.info(f"VK notification to {vk_user.vk_id} blocked by admin")
            return
        if not vk_user.notifications_enabled:
            logger.info(f"VK notification to {vk_user.vk_id} disabled in settings")
            return
        if not vk_user.is_subscribed:
            logger.info(f"VK notification to {vk_user.vk_id} skipped: guest is not subscribed to bot")
            return

        # 2.5. Определяем токен бота
        bot_token = None
        if vk_user.vk_group_id:
            bot = db.exec(select(VkBotConnection).where(VkBotConnection.vk_group_id == vk_user.vk_group_id, VkBotConnection.is_active == True)).first()
            if bot:
                bot_token = bot.vk_bot_token
                
        if not bot_token:
            main_bot = db.exec(select(VkBotConnection).where(VkBotConnection.is_main == True, VkBotConnection.is_active == True)).first()
            if main_bot:
                bot_token = main_bot.vk_bot_token
                
        if not bot_token:
            bot_token = vk_settings.vk_bot_token

        if not bot_token:
            logger.warning(f"No active VK bot connection found to send notification to user {vk_user.vk_id}")
            return

        vk_id = vk_user.vk_id

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


async def transfer_vk_points_to_iiko(db: Session, vk_user: VkUser, group_id: Optional[int], bot_token: str | None) -> str:
    """
    Переводит баллы активности ВК в бонусы iikoCard для пользователя.
    Списывает (обнуляет) локальные баллы и пополняет кошелек iiko.
    """
    from app.models.vk_activity_settings import VkActivitySettings
    from app.models.vk_activity import VkActivity
    from app.services.iiko_service import iiko_service
    from app.models.customer import Customer
    
    settings = None
    if group_id:
        settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == (conn.id if 'conn' in locals() and conn else 1))).first()
    if not settings:
        settings = db.exec(select(VkActivitySettings)).first()
        
    rate = settings.iiko_conversion_rate if settings else 1.0
    vk_points = vk_user.vk_bonus_balance or 0
    
    if vk_points <= 0:
        return "У вас нет накопленных баллов активности для перевода."
        
    bonus_value = round(vk_points * rate, 2)
    
    # 1. Запрос к iiko Cloud API для зачисления бонусов
    try:
        customer = db.exec(select(Customer).where(Customer.phone == vk_user.phone)).first()
        if not customer:
            return "Не найден гость в базе данных для вашего телефона."
            
        success = await iiko_service.add_customer_bonuses(
            customer.iiko_customer_id,
            bonus_value,
            f"Перевод баллов активности ВК ({vk_user.vk_id}) в бонусы"
        )
        # Успешно, если возвращен словарь без ошибки status == "error"
        is_ok = isinstance(success, dict) and success.get("status") != "error"
        if not is_ok:
            err_msg = success.get("message") if isinstance(success, dict) else None
            return f"Не удалось начислить бонусы в iikoCard: {err_msg}" if err_msg else "Не удалось начислить бонусы в iikoCard. Обратитесь в поддержку."
    except Exception as iiko_ex:
        logger.error(f"Error calling iiko topup in points transfer: {iiko_ex}")
        return f"Ошибка при подключении к API iiko: {str(iiko_ex)}"
        
    # 2. Обнуляем локальные баллы активности
    vk_user.vk_bonus_balance = 0
    vk_user.vk_bonus_balance_synced = 0
    db.add(vk_user)
    
    # 3. Записываем списание в историю активностей
    activity = VkActivity(
        vk_id=vk_user.vk_id,
        action_type="points_transfer",
        item_id=f"transfer_{int(utc_now().timestamp())}",
        points=-vk_points,
        is_synced=True
    )
    db.add(activity)
    
    # 4. Обновляем баланс гостя локально
    try:
        balance_info = await iiko_service.get_customer_balance(vk_user.phone)
        iiko_balance = balance_info.get("balance", 0)
        customer.bonus_points = iiko_balance
        db.add(customer)
    except Exception as bal_ex:
        logger.error(f"Failed to refresh customer balance after transfer: {bal_ex}")
        
    db.commit()
    
    return f"Успешно переведено {vk_points} баллов активности в {int(bonus_value)} бонусов iikoCard! 🎉"


async def link_phone_to_vk_user(db: Session, vk_id: int, phone: str, bot_token: str | None, group_id: Optional[int] = None, source: str = "verification") -> float:
    """Хелпер для привязки телефона к пользователю ВК и Customer с синхронизацией баланса iiko"""
    from app.models.vk_user import VkUser
    from app.models.customer import Customer
    from app.services.iiko_service import iiko_service
    
    # 1. Приведение к формату +7**********
    phone_digits = "".join(c for c in phone if c.isdigit())
    if len(phone_digits) == 11 and (phone_digits.startswith("8") or phone_digits.startswith("7")):
        phone_digits = "7" + phone_digits[1:]
    elif len(phone_digits) == 10 and phone_digits.startswith("9"):
        phone_digits = "7" + phone_digits
    db_phone = f"+{phone_digits}"
    
    # 2. Поиск гостя по телефону
    customer = db.exec(select(Customer).where(Customer.phone == db_phone)).first()
    now = utc_now()
    
    vk_profile = await fetch_vk_user_info(vk_id, bot_token) if bot_token else {}
    first_name = vk_profile.get("first_name") or "Гость"
    last_name = vk_profile.get("last_name") or ""
    
    if not customer:
        # Регистрация нового гостя в iiko и БД
        iiko_payload = {
            "phone": db_phone,
            "name": first_name,
            "surName": last_name,
            "sex": 0
        }
        res_id = None
        try:
            result = await iiko_service.create_or_update_customer(iiko_payload)
            res_id = result.get("id") or result.get("customer", {}).get("id")
        except Exception as ex:
            logger.error(f"Failed to create customer in iiko: {ex}")
            
        customer = Customer(
            phone=db_phone,
            name=first_name,
            surname=last_name,
            iiko_customer_id=res_id,
            vk_user_id=vk_id,
            bonus_points=0,
            created_at=now,
            updated_at=now
        )
        db.add(customer)
        db.commit()
        db.refresh(customer)
    else:
        customer.vk_user_id = vk_id
        db.add(customer)
        db.commit()
        
    # 3. Создаем/обновляем VkUser
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    if not vk_user:
        vk_user = VkUser(
            vk_id=vk_id,
            vk_group_id=group_id,
            phone=db_phone,
            iiko_customer_id=customer.iiko_customer_id,
            first_name=first_name,
            last_name=last_name,
            photo_50=vk_profile.get("photo_50"),
            screen_name=vk_profile.get("domain"),
            is_linked=True,
            linked_at=now,
            linking_source=source
        )
    else:
        vk_user.vk_group_id = group_id or vk_user.vk_group_id
        vk_user.phone = db_phone
        vk_user.iiko_customer_id = customer.iiko_customer_id
        vk_user.is_linked = True
        vk_user.linked_at = now
        vk_user.linking_source = source
        if not vk_user.first_name:
            vk_user.first_name = first_name
        if not vk_user.last_name:
            vk_user.last_name = last_name
        if vk_profile.get("photo_50"):
            vk_user.photo_50 = vk_profile.get("photo_50")
        if vk_profile.get("domain"):
            vk_user.screen_name = vk_profile.get("domain")
            
    db.add(vk_user)
    db.commit()
    db.refresh(vk_user)
    
    # Авто-синхронизация накопленных баллов активности ВК с iikoCard сразу при привязке
    try:
        from app.models.vk_activity_settings import VkActivitySettings
        from app.services.vk_activity_service import vk_activity_service
        
        settings = None
        if group_id:
            settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == (conn.id if 'conn' in locals() and conn else 1))).first()
        if not settings:
            settings = db.exec(select(VkActivitySettings)).first()
            
        # Авто-синхронизация при привязке телефона отключена
        # if settings and settings.sync_with_iiko and getattr(settings, "sync_on_verification", True):
        #     await vk_activity_service.sync_vk_user_points_to_iiko(db, vk_user, settings)
        #     db.refresh(vk_user)
    except Exception as sync_ex:
        logger.error(f"Error syncing VK points to iiko right after linking phone for user {vk_id}: {sync_ex}")
    
    # 4. Получение актуального объединяемого баланса
    points = 0
    try:
        balance_info = await iiko_service.get_customer_balance(db_phone)
        iiko_balance = balance_info.get("balance", 0)
        customer.bonus_points = iiko_balance
        db.add(customer)
        db.commit()
        
        summing_logic = getattr(settings, "iiko_summing_logic", "both") if settings else "both"
        rate = settings.iiko_conversion_rate if settings else 1.0
        synced_pts = vk_user.vk_bonus_balance_synced or 0
        
        if summing_logic == "both":
            points = float(iiko_balance) + (vk_user.vk_bonus_balance - synced_pts) * rate
        elif summing_logic == "vk_only":
            points = vk_user.vk_bonus_balance
        else:
            points = iiko_balance
    except Exception as ex:
        logger.error(f"Error syncing bonus balance: {ex}")
        points = customer.bonus_points
        
    return points


async def start_vk_verification(
    vk_id: int, 
    db: Session, 
    bot_token: str | None, 
    command_id: Optional[int] = None,
    message_text: Optional[str] = None
) -> bool:
    """Запуск Шага 1 верификации (Mini App / Lead Form) или каскада"""
    from app.models.validation_settings import ValidationSettings
    from app.models.bot_command import BotUserState
    import json
    
    settings = db.exec(select(ValidationSettings)).first()
    
    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
    unlinked_prefix = ""
    if vk_user and vk_user.vk_bonus_balance and vk_user.vk_bonus_balance > 0 and (not vk_user.vk_bonus_balance_synced or vk_user.vk_bonus_balance_synced < vk_user.vk_bonus_balance):
        unlinked_pts = int(vk_user.vk_bonus_balance - (vk_user.vk_bonus_balance_synced or 0))
        unlinked_prefix = f"У вас накоплено {unlinked_pts} баллов активности ВК! 🎁\nПривяжите номер телефона, чтобы перенести их на карту iikoCard и получить единый бонусный баланс.\n\n"

    # Если верификация глобально выключена, используем стандартное поведение (просто ввод телефона)
    if not settings or not settings.is_active:
        new_state = db.exec(
            select(BotUserState)
            .where(BotUserState.messenger == "vk")
            .where(BotUserState.peer_id == str(vk_id))
        ).first()
        if new_state:
            new_state.state = "awaiting_phone"
            new_state.command_id = command_id or new_state.command_id
        else:
            new_state = BotUserState(
                messenger="vk",
                peer_id=str(vk_id),
                state="awaiting_phone",
                command_id=command_id,
                context_data={}
            )
        db.add(new_state)
        db.commit()
        
        base_msg = message_text or (settings.vk_msg_start if settings else None) or "Ваш аккаунт не привязан к номеру телефона. Пожалуйста, отправьте ваш номер телефона (в формате 7**********) для привязки к карте гостя."
        req_phone = unlinked_prefix + base_msg
        await send_vk_message(vk_id=vk_id, message=req_phone, bot_token=bot_token)
        return True

    method = settings.vk_verification_method
    
    if method == "mini_app" and settings.vk_mini_app_id:
        new_state = db.exec(
            select(BotUserState)
            .where(BotUserState.messenger == "vk")
            .where(BotUserState.peer_id == str(vk_id))
        ).first()
        
        if new_state:
            new_state.state = "awaiting_auto_verification"
            new_state.command_id = command_id or new_state.command_id
        else:
            new_state = BotUserState(
                messenger="vk",
                peer_id=str(vk_id),
                state="awaiting_auto_verification",
                command_id=command_id,
                context_data={}
            )
        db.add(new_state)
        db.commit()
        
        keyboard = {
            "inline": True,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "open_link",
                            "link": f"https://vk.com/app{settings.vk_mini_app_id}",
                            "label": "⚡ Подтвердить в 1 клик"
                        }
                    }
                ],
                [
                    {
                        "action": {
                            "type": "text",
                            "payload": json.dumps({"action": "skip_auto_verification"}),
                            "label": "Другие способы подтверждения"
                        },
                        "color": "secondary"
                    }
                ]
            ]
        }
        msg = message_text or settings.vk_msg_start or "Для привязки карты гостя требуется подтвердить номер телефона. Пожалуйста, подтвердите его в 1 клик через наше приложение или выберите другой способ."
        await send_vk_message(
            vk_id=vk_id,
            message=msg,
            bot_token=bot_token,
            keyboard=keyboard
        )
        return True
        
    elif method == "lead_form" and settings.vk_lead_form_url:
        new_state = db.exec(
            select(BotUserState)
            .where(BotUserState.messenger == "vk")
            .where(BotUserState.peer_id == str(vk_id))
        ).first()
        
        if new_state:
            new_state.state = "awaiting_auto_verification"
            new_state.command_id = command_id or new_state.command_id
        else:
            new_state = BotUserState(
                messenger="vk",
                peer_id=str(vk_id),
                state="awaiting_auto_verification",
                command_id=command_id,
                context_data={}
            )
        db.add(new_state)
        db.commit()
        
        keyboard = {
            "inline": True,
            "buttons": [
                [
                    {
                        "action": {
                            "type": "text",
                            "payload": json.dumps({"action": "skip_auto_verification"}),
                            "label": "Другие способы подтверждения"
                        },
                        "color": "secondary"
                    }
                ]
            ]
        }
        
        msg_template = message_text or settings.vk_msg_start or f"Для привязки карты гостя требуется подтвердить номер телефона.\n\nПожалуйста, заполните короткую форму сбора заявок ВК (ВК автоматически подставит ваш реальный номер): {settings.vk_lead_form_url}"
        if "{url}" in msg_template:
            msg = msg_template.replace("{url}", settings.vk_lead_form_url or "")
        else:
            msg = msg_template
            if not message_text and not settings.vk_msg_start:
                # Если дефолтный шаблон и нет плейсхолдера, ссылка уже есть. Иначе если кастомный без плейсхолдера, допишем ссылку.
                pass
            elif settings.vk_msg_start and settings.vk_lead_form_url not in msg:
                msg = f"{msg}\n\n{settings.vk_lead_form_url}"
                
        await send_vk_message(
            vk_id=vk_id,
            message=msg,
            bot_token=bot_token,
            keyboard=keyboard
        )
        return True
        
    else:
        # Если авто-методы выключены, переходим к Шагу 2
        await send_vk_verification_methods(vk_id, db, bot_token, command_id)
        return True


async def send_vk_verification_methods(vk_id: int, db: Session, bot_token: str | None, command_id: int | None = None):
    """Вывод inline-клавиатуры выбора альтернативного способа верификации (Шаг 2)"""
    from app.models.validation_settings import ValidationSettings
    from app.models.bot_command import BotUserState
    import json
    
    settings = db.exec(select(ValidationSettings)).first()
    
    user_state = db.exec(
        select(BotUserState)
        .where(BotUserState.messenger == "vk")
        .where(BotUserState.peer_id == str(vk_id))
    ).first()
    
    if user_state:
        user_state.state = "awaiting_verification_method"
        user_state.command_id = command_id or user_state.command_id
    else:
        user_state = BotUserState(
            messenger="vk",
            peer_id=str(vk_id),
            state="awaiting_verification_method",
            command_id=command_id,
            context_data={}
        )
    db.add(user_state)
    db.commit()
    
    buttons = []
    
    # 1. Авто-метод (если настроен)
    if settings and settings.vk_verification_method in ("mini_app", "lead_form"):
        buttons.append([
            {
                "action": {
                    "type": "text",
                    "payload": json.dumps({"action": "vk_verify_auto"}),
                    "label": "VK Подтвердить"
                },
                "color": "primary"
            }
        ])
        
    # Разрешенные альтернативные каналы из настроек
    allowed_methods = ["fcall", "wcall", "tg", "max"]
    if settings and settings.vk_alternative_methods:
        allowed_methods = [m.strip() for m in settings.vk_alternative_methods.split(",") if m.strip()]
        
    # 2. Flash Call & Wait Call
    if "fcall" in allowed_methods:
        buttons.append([{
            "action": {
                "type": "text",
                "payload": json.dumps({"action": "vk_verify_fcall"}),
                "label": "📞 Звонок (Flash Call)"
            },
            "color": "secondary"
        }])
    if "wcall" in allowed_methods:
        buttons.append([{
            "action": {
                "type": "text",
                "payload": json.dumps({"action": "vk_verify_wcall"}),
                "label": "☎️ Набрать номер (Wait Call)"
            },
            "color": "secondary"
        }])
        
    # 3. Telegram & МАКС
    if "tg" in allowed_methods and settings and settings.telegram_bot_username:
        buttons.append([{
            "action": {
                "type": "text",
                "payload": json.dumps({"action": "vk_verify_tg"}),
                "label": "✈️ Через Telegram"
            },
            "color": "primary"
        }])
    if "max" in allowed_methods and settings and settings.max_bot_username:
        buttons.append([{
            "action": {
                "type": "text",
                "payload": json.dumps({"action": "vk_verify_max"}),
                "label": "💬 Через мессенджер МАКС"
            },
            "color": "primary"
        }])
        
    keyboard = {
        "inline": True,
        "buttons": buttons
    }
    
    msg = (settings.vk_msg_choose_method if settings and settings.vk_msg_choose_method 
           else "Не удалось получить номер автоматически. Пожалуйста, выберите другой удобный способ подтверждения:")
    
    await send_vk_message(
        vk_id=vk_id,
        message=msg,
        bot_token=bot_token,
        keyboard=keyboard
    )


async def handle_bot_commands_and_fsm(
    vk_id: int, 
    text: str, 
    db: Session, 
    bot_token: str | None, 
    group_id: Optional[int] = None,
    payload: Optional[dict] = None
) -> bool:
    """
    Обрабатывает входящие сообщения ВКонтакте согласно FSM и настроенным командам ботов.
    Возвращает True, если событие обработано ботом (дальнейший парсинг заказа не требуется).
    """
    try:
        from app.services.iiko_service import iiko_service
        from app.models.validation_settings import ValidationSettings
        from app.services.validation_service import validation_service
        import json
        import random
        
        now = utc_now()

        # 0. Проверяем состояние и команды новых маркетинговых ботов (NPS, ShopBot, Wheel, Referral)
        try:
            from app.services.vk_marketing_bots_service import VkMarketingBotsService
            from sqlmodel import text

            # А. Ожидание текста отзыва NPS (при оценке 1-3 звезды)
            nps_st = db.execute(text(f"SELECT * FROM vk_bot_user_states WHERE vk_id = {vk_id} AND state = 'awaiting_nps_feedback' LIMIT 1")).mappings().first()
            if nps_st:
                conn_nps = db.exec(select(VkBotConnection).where(VkBotConnection.is_active == True)).first()
                if conn_nps:
                    await VkMarketingBotsService.handle_nps_text_feedback(db, conn_nps, vk_id, text)
                    return True

            # Б. Обработка payload кнопок (NPS и ShopBot)
            if payload and isinstance(payload, dict):
                cmd_code = payload.get("cmd")
                if cmd_code == "nps_rate":
                    conn_cmd = db.exec(select(VkBotConnection).where(VkBotConnection.is_active == True)).first()
                    if conn_cmd:
                        await VkMarketingBotsService.handle_nps_rating(db, conn_cmd, vk_id, int(payload.get("rate", 5)), payload.get("order_id"))
                        return True
                elif cmd_code in ("shop_hits", "repeat_order", "order_status", "my_bonuses", "shop_promos", "call_manager", "carousel", "status_iiko", "bonus_balance", "operator"):
                    conn_cmd = db.exec(select(VkBotConnection).where(VkBotConnection.is_active == True)).first()
                    if conn_cmd:
                        await VkMarketingBotsService.handle_shop_command(db, conn_cmd, vk_id, cmd_code)
                        return True

            cleaned_msg = text.strip().lower()
            ref_param = message_obj.get("ref") if isinstance(message_obj, dict) else None

            conn_active = db.exec(select(VkBotConnection).where(VkBotConnection.is_active == True)).first()
            if conn_active:
                # В. Реферальный бот: переход по ссылке (ref=VR-...) или команда "пригласить друга", "рефералка"
                if ref_param or any(w in cleaned_msg for w in ("пригласить друга", "рефералка", "реферал")):
                    if await VkMarketingBotsService.handle_referral_command(db, conn_active, vk_id, ref_param=ref_param):
                        return True

                # Г. Колесо Фортуны: команда "крутить"
                if "крутить" in cleaned_msg or cleaned_msg == "wheel":
                    if await VkMarketingBotsService.spin_wheel_for_user(db, conn_active, vk_id, source="dm"):
                        return True

                # Д. Проверка текстовых триггеров каталога (меню, начать, старт, каталог)
                if any(k in cleaned_msg for k in ("меню", "начать", "start", "каталог", "заказать", "роллы")):
                    if await VkMarketingBotsService.send_shop_main_menu(db, conn_active, vk_id):
                        return True
        except Exception as bot_err:
            logger.warning(f"Ошибка роутинга маркетинговых ботов в vk_service: {bot_err}")

        # 1. Проверяем наличие активного FSM-состояния пользователя
        user_state = db.exec(
            select(BotUserState)
            .where(BotUserState.messenger == "vk")
            .where(BotUserState.peer_id == str(vk_id))
        ).first()

        if user_state:
            # Состояние ожидания комментария к отзыву
            if user_state.state == "awaiting_feedback_comment":
                order_id = user_state.context_data.get("order_id")
                rating = user_state.context_data.get("rating")
                
                vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
                customer_id = None
                if vk_user and vk_user.phone:
                    customer = db.exec(select(Customer).where(Customer.phone == vk_user.phone)).first()
                    if customer:
                        customer_id = customer.id
                
                review = db.exec(select(OrderReview).where(OrderReview.order_id == order_id)).first()
                if not review:
                    review = OrderReview(
                        order_id=order_id,
                        customer_id=customer_id,
                        rating=rating,
                        comment=text
                    )
                else:
                    review.comment = text
                    review.customer_id = customer_id or review.customer_id
                    
                db.add(review)
                db.delete(user_state)
                db.commit()
                
                await send_vk_message(
                    vk_id=vk_id,
                    message="Спасибо за ваш отзыв! Он поможет нам сделать наш сервис еще лучше! ❤️",
                    bot_token=bot_token
                )
                return True

            cmd = db.get(BotCommand, user_state.command_id) if user_state.command_id else None
            
            # --- НОВЫЕ СОСТОЯНИЯ ВЕРИФИКАЦИИ ---
            
            # 1. Состояние ожидания авто-верификации (Шаг 1)
            if user_state.state == "awaiting_auto_verification":
                action = payload.get("action") if payload else None
                if action == "skip_auto_verification" or text.strip().lower() == "другие способы подтверждения":
                    await send_vk_verification_methods(vk_id, db, bot_token, user_state.command_id)
                    return True
                
                # Если пришло что-то другое, напоминаем и повторно выводим кнопки Шага 1
                remind_text = "Пожалуйста, воспользуйтесь приложением для подтверждения в 1 клик или нажмите кнопку «Другие способы подтверждения»."
                await start_vk_verification(vk_id, db, bot_token, user_state.command_id, message_text=remind_text)
                return True
                
            # 2. Состояние выбора метода (Шаг 2)
            elif user_state.state == "awaiting_verification_method":
                action = payload.get("action") if payload else None
                cleaned_text = text.strip().lower()
                
                if action == "vk_verify_auto" or cleaned_text == "vk подтвердить":
                    await start_vk_verification(vk_id, db, bot_token, user_state.command_id)
                    return True
                    
                elif action == "vk_verify_fcall" or cleaned_text in ("звонок (flash call)", "flash call", "📞 звонок (flash call)"):
                    user_state.state = "awaiting_phone_for_fcall"
                    db.add(user_state)
                    db.commit()
                    
                    keyboard = {
                        "inline": True,
                        "buttons": [[{
                            "action": {
                                "type": "text",
                                "payload": json.dumps({"action": "skip_auto_verification"}),
                                "label": "Назад к выбору способов"
                            },
                            "color": "secondary"
                        }]]
                    }
                    settings = db.exec(select(ValidationSettings)).first()
                    msg = (settings.vk_msg_fcall_prompt if settings and settings.vk_msg_fcall_prompt 
                           else "Пожалуйста, введите ваш номер телефона строго с 7 (в формате 79*********), на который поступит входящий звонок-сброс. Пример: 79991234567")
                    await send_vk_message(
                        vk_id=vk_id,
                        message=msg,
                        bot_token=bot_token,
                        keyboard=keyboard
                    )
                    return True
                    
                elif action == "vk_verify_wcall" or cleaned_text in ("набрать номер (wait call)", "wait call", "☎️ набрать номер (wait call)"):
                    user_state.state = "awaiting_phone_for_wcall"
                    db.add(user_state)
                    db.commit()
                    
                    keyboard = {
                        "inline": True,
                        "buttons": [[{
                            "action": {
                                "type": "text",
                                "payload": json.dumps({"action": "skip_auto_verification"}),
                                "label": "Назад к выбору способов"
                            },
                            "color": "secondary"
                        }]]
                    }
                    settings = db.exec(select(ValidationSettings)).first()
                    msg = (settings.vk_msg_wcall_prompt if settings and settings.vk_msg_wcall_prompt 
                           else "Пожалуйста, введите ваш номер телефона строго с 7 (в формате 79*********), с которого вы будете звонить на наш виртуальный номер. Пример: 79991234567")
                    await send_vk_message(
                        vk_id=vk_id,
                        message=msg,
                        bot_token=bot_token,
                        keyboard=keyboard
                    )
                    return True
                    
                elif action == "vk_verify_tg" or cleaned_text in ("через telegram", "telegram", "✈️ через telegram"):
                    settings = db.exec(select(ValidationSettings)).first()
                    if settings and settings.telegram_bot_username:
                        link = f"https://t.me/{settings.telegram_bot_username}?start=VK{vk_id}"
                        keyboard = {
                            "inline": True,
                            "buttons": [[{
                                "action": {
                                    "type": "text",
                                    "payload": json.dumps({"action": "skip_auto_verification"}),
                                    "label": "Назад к выбору способов"
                                },
                                "color": "secondary"
                            }]]
                        }
                        msg_template = (settings.vk_msg_tg_instruct if settings and settings.vk_msg_tg_instruct 
                                       else "Для подтверждения через Telegram перейдите по ссылке ниже и нажмите «Запустить»/«Поделиться контактом»:\n\n{link}")
                        msg = msg_template.replace("{link}", link)
                        await send_vk_message(
                            vk_id=vk_id,
                            message=msg,
                            bot_token=bot_token,
                            keyboard=keyboard
                        )
                    else:
                        await send_vk_message(vk_id=vk_id, message="Метод авторизации через Telegram временно отключен.", bot_token=bot_token)
                    return True
                    
                elif action == "vk_verify_max" or cleaned_text in ("через мессенджер макс", "через макс", "💬 через мессенджер макс"):
                    settings = db.exec(select(ValidationSettings)).first()
                    if settings and settings.max_bot_username:
                        link = f"https://teams.vk.com/{settings.max_bot_username}?start=VK{vk_id}"
                        keyboard = {
                            "inline": True,
                            "buttons": [[{
                                "action": {
                                    "type": "text",
                                    "payload": json.dumps({"action": "skip_auto_verification"}),
                                    "label": "Назад к выбору способов"
                                },
                                "color": "secondary"
                            }]]
                        }
                        msg_template = (settings.vk_msg_max_instruct if settings and settings.vk_msg_max_instruct 
                                       else "Для подтверждения через мессенджер МАКС (VK Teams) перейдите по ссылке ниже:\n\n{link}")
                        msg = msg_template.replace("{link}", link)
                        await send_vk_message(
                            vk_id=vk_id,
                            message=msg,
                            bot_token=bot_token,
                            keyboard=keyboard
                        )
                    else:
                        await send_vk_message(vk_id=vk_id, message="Метод авторизации через МАКС временно отключен.", bot_token=bot_token)
                    return True
                    
                else:
                    await send_vk_verification_methods(vk_id, db, bot_token, user_state.command_id)
                    return True
                    
            # 3. Состояние ввода телефона для Flash Call
            elif user_state.state == "awaiting_phone_for_fcall":
                action = payload.get("action") if payload else None
                if action == "skip_auto_verification" or text.strip().lower() == "назад к выбору способов":
                    await send_vk_verification_methods(vk_id, db, bot_token, user_state.command_id)
                    return True
                    
                phone_digits = "".join(c for c in text if c.isdigit())
                if len(phone_digits) == 11 and (phone_digits.startswith("8") or phone_digits.startswith("7")):
                    phone_digits = "7" + phone_digits[1:]
                elif len(phone_digits) == 10 and phone_digits.startswith("9"):
                    phone_digits = "7" + phone_digits
                    
                if len(phone_digits) != 11 or not phone_digits.startswith("7"):
                    await send_vk_message(vk_id=vk_id, message="Некорректный формат. Пожалуйста, введите ваш номер телефона строго с 7 (в формате 79*********). Пример: 79991234567", bot_token=bot_token)
                    return True
                    
                db_phone = f"+{phone_digits}"
                code = str(random.randint(1000, 9999))
                
                # Отправляем Flash Call
                res = await validation_service.send_verification(db, db_phone, code, custom_route="fcall")
                if res.get("success"):
                    user_state.state = "awaiting_fcall_code"
                    user_state.context_data = {"phone": db_phone, "code": code}
                    db.add(user_state)
                    db.commit()
                    
                    keyboard = {
                        "inline": True,
                        "buttons": [[{
                            "action": {
                                "type": "text",
                                "payload": json.dumps({"action": "skip_auto_verification"}),
                                "label": "Назад к выбору способов"
                            },
                            "color": "secondary"
                        }]]
                    }
                    settings = db.exec(select(ValidationSettings)).first()
                    msg_template = (settings.vk_msg_fcall_code if settings and settings.vk_msg_fcall_code 
                                   else "На номер {phone} поступает входящий звонок. Пожалуйста, введите последние 4 цифры номера, который вам звонит:")
                    msg = msg_template.replace("{phone}", db_phone)
                    await send_vk_message(
                        vk_id=vk_id,
                        message=msg,
                        bot_token=bot_token,
                        keyboard=keyboard
                    )
                else:
                    err_msg = res.get("message") or "Ошибка отправки вызова."
                    await send_vk_message(vk_id=vk_id, message=f"Не удалось совершить звонок: {err_msg}", bot_token=bot_token)
                    await send_vk_verification_methods(vk_id, db, bot_token, user_state.command_id)
                return True
                
            # 4. Ожидание кода Flash Call
            elif user_state.state == "awaiting_fcall_code":
                action = payload.get("action") if payload else None
                if action == "skip_auto_verification" or text.strip().lower() == "назад к выбору способов":
                    await send_vk_verification_methods(vk_id, db, bot_token, user_state.command_id)
                    return True
                    
                entered_code = "".join(c for c in text if c.isdigit())
                expected_code = user_state.context_data.get("code")
                db_phone = user_state.context_data.get("phone")
                
                if entered_code == expected_code:
                    # Успех! Привязываем пользователя
                    points = await link_phone_to_vk_user(db, vk_id, db_phone, bot_token, group_id, source="fcall")
                    
                    if cmd and cmd.action_type == "transfer_points":
                        vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
                        msg_text = await transfer_vk_points_to_iiko(db, vk_user, group_id, bot_token)
                    else:
                        settings = db.exec(select(ValidationSettings)).first()
                        if settings and settings.vk_msg_success:
                            msg_text = settings.vk_msg_success.replace("{balance}", str(int(points)))
                        else:
                            balance_template = cmd.balance_text if cmd and cmd.balance_text else "Ваш бонусный баланс: {balance} бонусов."
                            msg_text = f"Проверка пройдена успешно!\n" + balance_template.replace("{balance}", str(int(points)))
                    await send_vk_message(vk_id=vk_id, message=msg_text, bot_token=bot_token)
                    
                    db.delete(user_state)
                    db.commit()
                else:
                    keyboard = {
                        "inline": True,
                        "buttons": [[{
                            "action": {
                                "type": "text",
                                "payload": json.dumps({"action": "skip_auto_verification"}),
                                "label": "Назад к выбору способов"
                            },
                            "color": "secondary"
                        }]]
                    }
                    settings = db.exec(select(ValidationSettings)).first()
                    msg = (settings.vk_msg_error_code if settings and settings.vk_msg_error_code 
                           else "Неверный код. Пожалуйста, проверьте последние 4 цифры входящего номера и введите их еще раз:")
                    await send_vk_message(
                        vk_id=vk_id,
                        message=msg,
                        bot_token=bot_token,
                        keyboard=keyboard
                    )
                return True
                
            # 5. Состояние ввода телефона для Wait Call
            elif user_state.state == "awaiting_phone_for_wcall":
                action = payload.get("action") if payload else None
                if action == "skip_auto_verification" or text.strip().lower() == "назад к выбору способов":
                    await send_vk_verification_methods(vk_id, db, bot_token, user_state.command_id)
                    return True
                    
                phone_digits = "".join(c for c in text if c.isdigit())
                if len(phone_digits) == 11 and (phone_digits.startswith("8") or phone_digits.startswith("7")):
                    phone_digits = "7" + phone_digits[1:]
                elif len(phone_digits) == 10 and phone_digits.startswith("9"):
                    phone_digits = "7" + phone_digits
                    
                if len(phone_digits) != 11 or not phone_digits.startswith("7"):
                    await send_vk_message(vk_id=vk_id, message="Некорректный формат. Пожалуйста, введите ваш номер телефона строго с 7 (в формате 79*********). Пример: 79991234567", bot_token=bot_token)
                    return True
                    
                db_phone = f"+{phone_digits}"
                
                # Инициируем Wait Call сессию
                res = await validation_service.send_verification(db, db_phone, code="1111", custom_route="wcall")
                phone_to_call = res.get("phone_to_call")
                
                if res.get("success") and phone_to_call:
                    user_state.state = "awaiting_wait_call"
                    user_state.context_data = {"phone": db_phone, "uuid": res.get("uuid")}
                    db.add(user_state)
                    db.commit()
                    
                    keyboard = {
                        "inline": True,
                        "buttons": [[{
                            "action": {
                                "type": "text",
                                "payload": json.dumps({"action": "skip_auto_verification"}),
                                "label": "Назад к выбору способов"
                            },
                            "color": "secondary"
                        }]]
                    }
                    
                    # Приводим к формату +79********* для легкого клика
                    formatted_phone_to_call = phone_to_call
                    digits = "".join(c for c in phone_to_call if c.isdigit())
                    if len(digits) == 11 and (digits.startswith("7") or digits.startswith("8")):
                        formatted_phone_to_call = f"+7{digits[1:]}"
                    elif len(digits) == 10:
                        formatted_phone_to_call = f"+7{digits}"
                    
                    settings = db.exec(select(ValidationSettings)).first()
                    msg_template = (settings.vk_msg_wcall_instruct if settings and settings.vk_msg_wcall_instruct 
                                   else "Пожалуйста, совершите бесплатный вызов со своего номера {phone} на виртуальный номер:\n\n{call_phone}\n\nСистема распознает ваш звонок, автоматически сбросит его и подтвердит ваш профиль.")
                    msg = msg_template.replace("{phone}", db_phone).replace("{call_phone}", formatted_phone_to_call)
                    await send_vk_message(vk_id=vk_id, message=msg, bot_token=bot_token, keyboard=keyboard)
                else:
                    err_msg = res.get("message") or "Не удалось инициировать Wait Call."
                    await send_vk_message(vk_id=vk_id, message=f"Ошибка телефонии: {err_msg}", bot_token=bot_token)
                    await send_vk_verification_methods(vk_id, db, bot_token, user_state.command_id)
                return True
                
            # 6. Состояние ожидания звонка Wait Call
            elif user_state.state == "awaiting_wait_call":
                action = payload.get("action") if payload else None
                if action == "skip_auto_verification" or text.strip().lower() == "назад к выбору способов":
                    await send_vk_verification_methods(vk_id, db, bot_token, user_state.command_id)
                    return True
                    
                db_phone = user_state.context_data.get("phone")
                await send_vk_message(
                    vk_id=vk_id,
                    message=f"Ожидаем ваш звонок с номера {db_phone}.\nЕсли вы не можете позвонить, нажмите кнопку «Назад к выбору способов» ниже.",
                    bot_token=bot_token
                )
                return True

            # Состояние А: Ожидание ввода телефона (классическое ручное подтверждение)
            elif user_state.state == "awaiting_phone":
                phone_digits = "".join(c for c in text if c.isdigit())
                
                # Приведение к формату 7********** (11 цифр)
                if len(phone_digits) == 11 and (phone_digits.startswith("8") or phone_digits.startswith("7")):
                    phone_digits = "7" + phone_digits[1:]
                elif len(phone_digits) == 10 and phone_digits.startswith("9"):
                    phone_digits = "7" + phone_digits
                
                # Валидация
                if len(phone_digits) != 11 or not phone_digits.startswith("7"):
                    await send_vk_message(
                        vk_id=vk_id,
                        message="Пожалуйста, введите корректный номер телефона (11 цифр, начиная с 7 или 8), например: 79991234567.",
                        bot_token=bot_token
                    )
                    return True
                
                # Поиск в базе гостей
                db_phone = f"+{phone_digits}"
                customer = db.exec(select(Customer).where(Customer.phone == db_phone)).first()
                
                if customer:
                    # А1. Связываем аккаунт ВК с найденным гостем
                    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
                    vk_profile = await fetch_vk_user_info(vk_id, bot_token) if bot_token else {}
                    
                    if not vk_user:
                        vk_user = VkUser(
                            vk_id=vk_id,
                            vk_group_id=group_id,
                            phone=customer.phone,
                            iiko_customer_id=str(customer.id),
                            first_name=vk_profile.get("first_name") or customer.name,
                            last_name=vk_profile.get("last_name"),
                            photo_50=vk_profile.get("photo_50"),
                            screen_name=vk_profile.get("domain"),
                            is_linked=True,
                            linked_at=now,
                            linking_source="bot_phone_link"
                        )
                    else:
                        vk_user.vk_group_id = group_id or vk_user.vk_group_id
                        vk_user.phone = customer.phone
                        vk_user.iiko_customer_id = str(customer.id)
                        vk_user.first_name = vk_profile.get("first_name") or vk_user.first_name or customer.name
                        vk_user.last_name = vk_profile.get("last_name") or vk_user.last_name
                        vk_user.photo_50 = vk_profile.get("photo_50") or vk_user.photo_50
                        vk_user.screen_name = vk_profile.get("domain") or vk_user.screen_name
                        vk_user.is_linked = True
                        vk_user.linked_at = now
                        vk_user.linking_source = "bot_phone_link"
                    
                    db.add(vk_user)
                    customer.vk_user_id = vk_id
                    db.add(customer)
                    db.commit()
                    
                    # Авто-синхронизация накопленных баллов активности ВК с iikoCard при связывании по номеру
                    points = 0
                    try:
                        from app.models.vk_activity_settings import VkActivitySettings
                        from app.services.vk_activity_service import vk_activity_service
                        
                        settings = None
                        if group_id:
                            settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == (conn.id if 'conn' in locals() and conn else 1))).first()
                        if not settings:
                            settings = db.exec(select(VkActivitySettings)).first()
                            
                        # Авто-синхронизация при верификации отключена
                        # if settings and settings.sync_with_iiko and getattr(settings, "sync_on_verification", True):
                        #     await vk_activity_service.sync_vk_user_points_to_iiko(db, vk_user, settings)
                        #     db.refresh(vk_user)
                            
                        balance_info = await iiko_service.get_customer_balance(customer.phone)
                        iiko_balance = balance_info.get("balance", 0)
                        customer.bonus_points = iiko_balance
                        db.add(customer)
                        db.commit()
                        
                        summing_logic = getattr(settings, "iiko_summing_logic", "both") if settings else "both"
                        rate = settings.iiko_conversion_rate if settings else 1.0
                        synced_pts = vk_user.vk_bonus_balance_synced or 0
                        
                        if summing_logic == "both":
                            points = float(iiko_balance) + (vk_user.vk_bonus_balance - synced_pts) * rate
                        elif summing_logic == "vk_only":
                            points = vk_user.vk_bonus_balance
                        else:
                            points = iiko_balance
                    except Exception as ex:
                        logger.error(f"Error syncing bonus balance during bot link: {ex}")
                        points = customer.bonus_points
                        
                    # Отправляем успешный баланс
                    balance_template = cmd.balance_text if cmd and cmd.balance_text else "Ваш бонусный баланс: {balance} бонусов."
                    msg_text = balance_template.replace("{balance}", str(int(points)))
                    await send_vk_message(vk_id=vk_id, message=msg_text, bot_token=bot_token)
                    
                    # Удаляем состояние
                    db.delete(user_state)
                    db.commit()
                    return True
                else:
                    # А2. Номер не найден, предлагаем регистрацию
                    user_state.state = "awaiting_register_confirm"
                    user_state.context_data = {"phone": phone_digits}
                    db.add(user_state)
                    db.commit()
                    
                    phone_not_found = cmd.phone_not_found_text if cmd and cmd.phone_not_found_text else "К сожалению, данный номер в базе не определен."
                    reg_confirm = cmd.register_confirm_text if cmd and cmd.register_confirm_text else "Хотите зарегистрироваться в нашей бонусной системе? Ответьте Да или Нет."
                    await send_vk_message(
                        vk_id=vk_id,
                        message=f"{phone_not_found}\n{reg_confirm}",
                        bot_token=bot_token
                    )
                    return True
            
            # Состояние Б: Ожидание подтверждения регистрации (Да / Нет)
            elif user_state.state == "awaiting_register_confirm":
                reply = text.strip().lower()
                
                if reply == "да":
                    # Регистрация гостя
                    phone_digits = user_state.context_data.get("phone")
                    db_phone = f"+{phone_digits}"
                    
                    vk_profile = await fetch_vk_user_info(vk_id, bot_token) if bot_token else {}
                    first_name = vk_profile.get("first_name") or "Гость"
                    last_name = vk_profile.get("last_name") or ""
                    
                    # 1. Создаем в iiko
                    iiko_payload = {
                        "phone": db_phone,
                        "name": first_name,
                        "surName": last_name,
                        "sex": 0
                    }
                    
                    res_id = None
                    try:
                        result = await iiko_service.create_or_update_customer(iiko_payload)
                        res_id = result.get("id") or result.get("customer", {}).get("id")
                    except Exception as ex:
                        logger.error(f"Failed to create customer in iiko during bot register: {ex}")
                    
                    # 2. Создаем Customer локально
                    new_customer = Customer(
                        phone=db_phone,
                        name=first_name,
                        surname=last_name,
                        iiko_customer_id=res_id,
                        vk_user_id=vk_id,
                        bonus_points=0,
                        created_at=now,
                        updated_at=now
                    )
                    db.add(new_customer)
                    db.commit()
                    db.refresh(new_customer)
                    
                    # 3. Обновляем/создаем VkUser
                    vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
                    if not vk_user:
                        vk_user = VkUser(
                            vk_id=vk_id,
                            vk_group_id=group_id,
                            phone=db_phone,
                            iiko_customer_id=res_id,
                            first_name=first_name,
                            last_name=last_name,
                            photo_50=vk_profile.get("photo_50"),
                            screen_name=vk_profile.get("domain"),
                            is_linked=True,
                            linked_at=now,
                            linking_source="bot_register"
                        )
                    else:
                        vk_user.vk_group_id = group_id or vk_user.vk_group_id
                        vk_user.phone = db_phone
                        vk_user.iiko_customer_id = res_id
                        vk_user.first_name = first_name
                        vk_user.last_name = last_name
                        vk_user.photo_50 = vk_profile.get("photo_50") or vk_user.photo_50
                        vk_user.screen_name = vk_profile.get("domain") or vk_user.screen_name
                        vk_user.is_linked = True
                        vk_user.linked_at = now
                        vk_user.linking_source = "bot_register"
                    db.add(vk_user)
                    db.commit()
                    
                    # Авто-синхронизация накопленных баллов активности ВК с iikoCard при регистрации
                    points = 0
                    try:
                        from app.models.vk_activity_settings import VkActivitySettings
                        from app.services.vk_activity_service import vk_activity_service
                        
                        settings = None
                        if group_id:
                            settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == (conn.id if 'conn' in locals() and conn else 1))).first()
                        if not settings:
                            settings = db.exec(select(VkActivitySettings)).first()
                            
                        # Авто-синхронизация при регистрации отключена
                        # if settings and settings.sync_with_iiko and getattr(settings, "sync_on_verification", True):
                        #     await vk_activity_service.sync_vk_user_points_to_iiko(db, vk_user, settings)
                        #     db.refresh(vk_user)
                            
                        balance_info = await iiko_service.get_customer_balance(db_phone)
                        iiko_balance = balance_info.get("balance", 0)
                        new_customer.bonus_points = iiko_balance
                        db.add(new_customer)
                        db.commit()
                        
                        summing_logic = getattr(settings, "iiko_summing_logic", "both") if settings else "both"
                        rate = settings.iiko_conversion_rate if settings else 1.0
                        synced_pts = vk_user.vk_bonus_balance_synced or 0
                        
                        if summing_logic == "both":
                            points = float(iiko_balance) + (vk_user.vk_bonus_balance - synced_pts) * rate
                        elif summing_logic == "vk_only":
                            points = vk_user.vk_bonus_balance
                        else:
                            points = iiko_balance
                    except Exception as sync_ex:
                        logger.error(f"Error syncing VK points during bot register confirmation: {sync_ex}")
                        points = new_customer.bonus_points

                    # Отправляем сообщение об успешной регистрации
                    if cmd and cmd.action_type == "transfer_points":
                        msg_text = await transfer_vk_points_to_iiko(db, vk_user, group_id, bot_token)
                    else:
                        success_template = cmd.register_success_text if cmd and cmd.register_success_text else "Вы успешно зарегистрированы в нашей бонусной системе! Ваш бонусный баланс: {balance} бонусов."
                        msg_text = success_template.replace("{balance}", str(int(points)))
                    await send_vk_message(vk_id=vk_id, message=msg_text, bot_token=bot_token)
                    
                    # Удаляем состояние
                    db.delete(user_state)
                    db.commit()
                    return True
                    
                elif reply == "нет":
                    await send_vk_message(
                        vk_id=vk_id,
                        message="Регистрация отменена. Вы можете запросить баланс позже, написав команду заново.",
                        bot_token=bot_token
                    )
                    # Удаляем состояние
                    db.delete(user_state)
                    db.commit()
                    return True
                else:
                    await send_vk_message(
                        vk_id=vk_id,
                        message="Пожалуйста, ответьте Да или Нет.",
                        bot_token=bot_token
                    )
                    return True
        
        # 2. Если FSM-состояния нет, ищем триггерную команду
        commands = db.exec(select(BotCommand).where(BotCommand.is_active == True)).all()
        matching_cmd = None
        
        cleaned_text = text.strip().lower()
        for cmd in commands:
            if "vk" in cmd.channels and cmd.trigger_phrase.strip().lower() == cleaned_text:
                matching_cmd = cmd
                break
                
        if matching_cmd:
            if matching_cmd.action_type == "custom_text":
                # Кастомный ответ
                if matching_cmd.response_text:
                    await send_vk_message(vk_id=vk_id, message=matching_cmd.response_text, bot_token=bot_token)
                return True
                
            elif matching_cmd.action_type == "get_balance":
                # Логика бонусного баланса
                vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
                
                # Если пользователь привязан и есть телефон
                if vk_user and vk_user.is_linked and vk_user.phone:
                    try:
                        # Получаем настройки активности
                        from app.models.vk_activity_settings import VkActivitySettings
                        from app.services.vk_activity_service import vk_activity_service
                        
                        settings = None
                        if vk_user.vk_group_id:
                            settings = db.exec(select(VkActivitySettings).where(VkActivitySettings.vk_bot_connection_id == vk_user.vk_group_id)).first()
                        if not settings:
                            settings = db.exec(select(VkActivitySettings)).first()

                        # Авто-синхронизация при запросе баланса отключена
                        try:
                            # if settings and settings.sync_with_iiko and getattr(settings, "sync_on_balance_request", True):
                            #     await vk_activity_service.sync_vk_user_points_to_iiko(db, vk_user, settings)
                            #     db.refresh(vk_user)
                            pass
                        except Exception as sync_ex:
                            logger.error(f"Error auto-syncing points during get_balance check: {sync_ex}")

                        balance_info = await iiko_service.get_customer_balance(vk_user.phone)
                        iiko_balance = balance_info.get("balance", 0)
                        
                        customer = db.exec(select(Customer).where(Customer.phone == vk_user.phone)).first()
                        if customer:
                            customer.bonus_points = iiko_balance
                            db.add(customer)
                            db.commit()
                            
                        # Применяем логику суммирования и отображения
                        summing_logic = getattr(settings, "iiko_summing_logic", "both") if settings else "both"
                        rate = settings.iiko_conversion_rate if settings else 1.0
                        synced_pts = vk_user.vk_bonus_balance_synced or 0
                        
                        if summing_logic == "both":
                            points = float(iiko_balance) + (vk_user.vk_bonus_balance - synced_pts) * rate
                        elif summing_logic == "vk_only":
                            points = vk_user.vk_bonus_balance
                        else:  # iiko_only
                            points = iiko_balance
                    except Exception as ex:
                        logger.error(f"Error syncing bonus balance for VK user {vk_id}: {ex}")
                        customer = db.exec(select(Customer).where(Customer.phone == vk_user.phone)).first()
                        points = customer.bonus_points if customer else 0
                        
                    balance_template = matching_cmd.balance_text if matching_cmd.balance_text else "Ваш бонусный баланс: {balance} бонусов."
                    msg_text = balance_template.replace("{balance}", str(int(points)))
                    await send_vk_message(vk_id=vk_id, message=msg_text, bot_token=bot_token)
                    return True
                else:
                    # ЗАПУСК ВЕРИФИКАЦИИ (ШАГ 1 ИЛИ ШАГ 2)
                    await start_vk_verification(vk_id, db, bot_token, matching_cmd.id)
                    return True

            elif matching_cmd.action_type == "transfer_points":
                # Логика перевода баллов активности в бонусы iiko
                vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
                
                # Если пользователь привязан и есть телефон
                if vk_user and vk_user.is_linked and vk_user.phone:
                    msg_text = await transfer_vk_points_to_iiko(db, vk_user, group_id, bot_token)
                    await send_vk_message(vk_id=vk_id, message=msg_text, bot_token=bot_token)
                    return True
                else:
                    # Запуск верификации (точно так же как get_balance)
                    await start_vk_verification(vk_id, db, bot_token, matching_cmd.id)
                    return True

            elif matching_cmd.action_type == "unlink_phone":
                # Логика отвязки телефона
                vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
                if vk_user and vk_user.is_linked:
                    if vk_user.phone:
                        customer = db.exec(select(Customer).where(Customer.phone == vk_user.phone)).first()
                        if customer and customer.vk_user_id == vk_id:
                            customer.vk_user_id = None
                            db.add(customer)
                    
                    vk_user.is_linked = False
                    vk_user.phone = None
                    vk_user.iiko_customer_id = None
                    vk_user.linking_source = None
                    vk_user.linked_at = None
                    db.add(vk_user)
                    db.commit()
                    
                    response_text = matching_cmd.response_text if matching_cmd.response_text else "Ваш номер телефона успешно отвязан от аккаунта. Для повторной привязки отправьте команду узнать баланс."
                    await send_vk_message(vk_id=vk_id, message=response_text, bot_token=bot_token)
                else:
                    response_text = "Ваш аккаунт не был привязан к номеру телефона."
                    await send_vk_message(vk_id=vk_id, message=response_text, bot_token=bot_token)
                return True
                    
    except Exception as ex:
        logger.error(f"Error handling bot commands and FSM for VK user {vk_id}: {ex}")
        
    return False


async def handle_rate_order_payload(vk_id: int, payload: dict, db: Session, bot_token: str | None, group_id: Optional[int] = None):
    try:
        order_id = payload.get("order_id")
        rating = int(payload.get("rating", 0))
        
        vk_user = db.exec(select(VkUser).where(VkUser.vk_id == vk_id)).first()
        customer_id = None
        if vk_user and vk_user.phone:
            customer = db.exec(select(Customer).where(Customer.phone == vk_user.phone)).first()
            if customer:
                customer_id = customer.id
                
        # Создаем или обновляем отзыв OrderReview
        review = db.exec(select(OrderReview).where(OrderReview.order_id == order_id)).first()
        if not review:
            review = OrderReview(
                order_id=order_id,
                customer_id=customer_id,
                rating=rating
            )
        else:
            review.rating = rating
            review.customer_id = customer_id or review.customer_id
            
        db.add(review)
        
        user_state = db.exec(
            select(BotUserState)
            .where(BotUserState.messenger == "vk")
            .where(BotUserState.peer_id == str(vk_id))
        ).first()
        
        if user_state:
            user_state.state = "awaiting_feedback_comment"
            user_state.context_data = {"order_id": order_id, "rating": rating}
            db.add(user_state)
        else:
            new_state = BotUserState(
                messenger="vk",
                peer_id=str(vk_id),
                state="awaiting_feedback_comment",
                context_data={"order_id": order_id, "rating": rating}
            )
            db.add(new_state)
            
        db.commit()
        
        await send_vk_message(
            vk_id=vk_id,
            message=f"Вы поставили оценку {rating}⭐.\nПожалуйста, напишите в ответном сообщении ваш комментарий к заказу (что вам понравилось или что нам стоит улучшить). Ваше мнение очень важно для нас!",
            bot_token=bot_token
        )
    except Exception as e:
        logger.error(f"Error handling rate order payload: {e}")
        db.rollback()


async def handle_message_event(obj: Dict[str, Any], db: Session, bot_token: str | None, group_id: Optional[int] = None):
    vk_id = obj.get("user_id")
    payload = obj.get("payload")
    event_id = obj.get("event_id")
    peer_id = obj.get("peer_id")
    
    if not vk_id or not payload:
        return
        
    try:
        import json
        if isinstance(payload, str):
            payload = json.loads(payload)

        if isinstance(payload, dict) and payload.get("cmd") == "courier_deliver":
            order_id = payload.get("order_id")
            pay = payload.get("pay") or "paid"
            if order_id:
                from app.services.vk_notification_router import handle_courier_order_action
                await handle_courier_order_action(int(order_id), str(pay), "vk", str(vk_id))
            if event_id and bot_token:
                url = "https://api.vk.ru/method/messages.sendMessageEventAnswer"
                params = {
                    "event_id": event_id,
                    "user_id": vk_id,
                    "peer_id": peer_id or vk_id,
                    "event_data": json.dumps({"type": "show_snackbar", "text": "✅ Заказ отмечен как доставленный!"}, ensure_ascii=False),
                    "access_token": bot_token,
                    "v": "5.199"
                }
                async with httpx.AsyncClient(timeout=5.0) as client:
                    await client.post(url, data=params)
            return
            
        if isinstance(payload, dict) and payload.get("action") == "rate_order":
            await handle_rate_order_payload(vk_id, payload, db, bot_token, group_id)
            
            if event_id and bot_token:
                url = "https://api.vk.ru/method/messages.sendMessageEventAnswer"
                params = {
                    "event_id": event_id,
                    "user_id": vk_id,
                    "peer_id": peer_id or vk_id,
                    "access_token": bot_token,
                    "v": "5.199"
                }
                async with httpx.AsyncClient() as client:
                    await client.post(url, data=params)
    except Exception as e:
        logger.error(f"Error handling message_event: {e}")


async def send_miniapp_push(
    db: Session,
    user_ids: List[int],
    message: str,
    fragment: Optional[str] = None
) -> Dict[str, Any]:
    """
    Отправляет нативное Push-уведомление пользователям VK Mini App (через API secure.sendNotification).
    
    :param db: Сессия базы данных
    :param user_ids: Список VK User ID получателей
    :param message: Текст сообщения (до 254 символов)
    :param fragment: fragment (хэш-путь) запуска приложения (например, '/orders/123')
    """
    from app.models.validation_settings import ValidationSettings
    
    if not user_ids:
        return {"success": False, "error": "empty_user_ids"}
        
    # 1. Получаем настройки Mini App
    settings = db.exec(select(ValidationSettings)).first()
    if not settings or not settings.vk_mini_app_id or not settings.vk_mini_app_secret:
        logger.warning("[VK Push] Mini App settings (ID or Secret) are not configured in validation_settings")
        return {"success": False, "error": "not_configured"}
        
    app_id = settings.vk_mini_app_id
    app_secret = settings.vk_mini_app_secret
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            # 2. Получаем сервисный access_token приложения (client credentials flow)
            token_url = "https://oauth.vk.ru/access_token"
            token_params = {
                "client_id": app_id,
                "client_secret": app_secret,
                "grant_type": "client_credentials"
            }
            token_res = await client.get(token_url, params=token_params)
            token_res.raise_for_status()
            token_data = token_res.json()
            
            service_token = token_data.get("access_token")
            if not service_token:
                raise ValueError("Failed to retrieve service access_token from VK response")
                
            # 3. Отправляем уведомления (по спецификации ВК можно слать пачками до 100 ID)
            # Разбиваем список пользователей на части по 100 элементов
            chunk_size = 100
            user_ids_chunks = [user_ids[i:i + chunk_size] for i in range(0, len(user_ids), chunk_size)]
            
            send_results = []
            for chunk in user_ids_chunks:
                notification_url = "https://api.vk.ru/method/secure.sendNotification"
                payload = {
                    "user_ids": ",".join(map(str, chunk)),
                    "message": message[:250],  # Лимит ВК составляет 254 символа
                    "access_token": service_token,
                    "v": "5.199"
                }
                if fragment:
                    payload["fragment"] = fragment
                    
                res = await client.post(notification_url, data=payload)
                res.raise_for_status()
                res_data = res.json()
                
                if "error" in res_data:
                    logger.error(f"[VK Push] VK API returned error: {res_data['error']}")
                    send_results.append({"success": False, "chunk": chunk, "error": res_data["error"]})
                else:
                    logger.info(f"[VK Push] Notification sent successfully to chunk: {chunk}")
                    send_results.append({"success": True, "chunk": chunk, "response": res_data.get("response")})
                    
            return {"success": True, "results": send_results}
            
    except Exception as e:
        logger.error(f"[VK Push] Failed to send VK Mini App Push notification: {e}", exc_info=True)
        return {"success": False, "error": str(e)}

