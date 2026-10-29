"""
Сервис взаимодействия с мессенджером MAX
Поддерживает официальный Bot API (platform-api2.max.ru) и интеллектуальную маршрутизацию сообщений
с записью в журнал max_message_logs.
"""
import logging
import json
import httpx
from typing import Optional, List, Dict, Any
from sqlmodel import Session, select
from app.models.max_settings import MaxSettings, MaxBot, MaxMessageLog
from app.models.customer import Customer
from app.services.max_bridge_service import max_bridge_service

logger = logging.getLogger(__name__)

DEFAULT_MAX_BASE_URL = "https://platform-api2.max.ru"


def _clean_phone_number(phone: str) -> str:
    """Нормализация номера телефона к формату 7XXXXXXXXXX"""
    digits = "".join(filter(str.isdigit, str(phone)))
    if len(digits) == 11 and digits.startswith("8"):
        return "7" + digits[1:]
    if len(digits) == 10:
        return "7" + digits
    return digits


async def verify_bot_token(token: str, base_url: str = DEFAULT_MAX_BASE_URL) -> Dict[str, Any]:
    """
    Проверка токена бота MAX через официальный эндпоинт GET /me.
    Возвращает информацию о боте: user_id, name, username, commands, avatar_url.
    """
    url = f"{base_url.rstrip('/')}/me"
    headers = {
        "Authorization": token.strip(),
        "Content-Type": "application/json"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                data = response.json()
                return {
                    "valid": True,
                    "bot_id": str(data.get("user_id") or data.get("id") or ""),
                    "bot_name": data.get("name") or data.get("first_name") or "Бот MAX",
                    "bot_username": data.get("username") or "",
                    "bot_avatar": data.get("avatar_url") or "",
                    "commands": data.get("commands") or [],
                    "raw": data
                }
            return {
                "valid": False,
                "error": f"Ошибка {response.status_code}: {response.text}"
            }
    except Exception as e:
        logger.error(f"Ошибка проверки токена бота MAX: {e}")
        return {"valid": False, "error": str(e)}


async def get_bot_subscriptions(token: str, base_url: str = DEFAULT_MAX_BASE_URL) -> List[Dict[str, Any]]:
    """Получение текущих подписок Webhook для бота"""
    url = f"{base_url.rstrip('/')}/subscriptions"
    headers = {"Authorization": token.strip()}
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.get(url, headers=headers)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("subscriptions", []) if isinstance(data, dict) else []
            return []
    except Exception as e:
        logger.warning(f"Ошибка получения подписок бота MAX: {e}")
        return []


async def set_bot_webhook(token: str, webhook_url: str, base_url: str = DEFAULT_MAX_BASE_URL) -> Dict[str, Any]:
    """
    Установка/регистрация Webhook URL для бота через POST /subscriptions
    """
    url = f"{base_url.rstrip('/')}/subscriptions"
    headers = {
        "Authorization": token.strip(),
        "Content-Type": "application/json"
    }
    payload = {
        "url": webhook_url.strip(),
        "version": "2"
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.post(url, headers=headers, json=payload)
            if resp.status_code in [200, 201]:
                return {"success": True, "data": resp.json()}
            return {"success": False, "error": f"Статус {resp.status_code}: {resp.text}"}
    except Exception as e:
        logger.error(f"Ошибка установки вебхука MAX: {e}")
        return {"success": False, "error": str(e)}


async def delete_bot_webhook(token: str, webhook_url: Optional[str] = None, base_url: str = DEFAULT_MAX_BASE_URL) -> Dict[str, Any]:
    """Удаление подписки Webhook бота"""
    base_sub = f"{base_url.rstrip('/')}/subscriptions"
    headers = {"Authorization": token.strip()}
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            if webhook_url:
                resp = await client.delete(f"{base_sub}?url={webhook_url.strip()}", headers=headers)
            else:
                # Получаем все подписки и удаляем
                subs = await get_bot_subscriptions(token, base_url)
                for s in subs:
                    u = s.get("url")
                    if u:
                        await client.delete(f"{base_sub}?url={u}", headers=headers)
                return {"success": True, "deleted_count": len(subs)}
            return {"success": resp.status_code in [200, 204], "response": resp.text}
    except Exception as e:
        logger.error(f"Ошибка удаления вебхука MAX: {e}")
        return {"success": False, "error": str(e)}


async def set_bot_commands(token: str, commands: List[Dict[str, str]], base_url: str = DEFAULT_MAX_BASE_URL) -> Dict[str, Any]:
    """
    Установка списка команд бота через PATCH /me
    Каждая команда имеет вид: {"name": "start", "description": "Запустить бота"}
    """
    url = f"{base_url.rstrip('/')}/me"
    headers = {
        "Authorization": token.strip(),
        "Content-Type": "application/json"
    }
    payload = {"commands": commands}
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.patch(url, headers=headers, json=payload)
            if resp.status_code == 200:
                return {"success": True, "data": resp.json()}
            return {"success": False, "error": f"Статус {resp.status_code}: {resp.text}"}
    except Exception as e:
        logger.error(f"Ошибка сохранения команд бота MAX: {e}")
        return {"success": False, "error": str(e)}



async def upload_max_bot_image(token: str, image_path: str, base_url: str = DEFAULT_MAX_BASE_URL) -> Optional[Dict[str, Any]]:
    """
    Загрузка изображения на сервера MAX Bot API через POST /uploads?type=image.
    """
    import os
    if not image_path or not os.path.exists(image_path):
        return None
    url = f"{base_url.rstrip('/')}/uploads?type=image"
    headers = {"Authorization": token.strip()}
    try:
        filename = os.path.basename(image_path)
        with open(image_path, "rb") as f:
            file_bytes = f.read()
        files = {"file": (filename, file_bytes, "image/png")}
        async with httpx.AsyncClient(timeout=15.0, verify=False) as client:
            resp = await client.post(url, headers=headers, files=files)
            if resp.status_code in [200, 201]:
                res_data = resp.json()
                return {"type": "image", "payload": res_data}
            else:
                logger.warning(f"MAX Bot upload image returned HTTP {resp.status_code}: {resp.text}")
    except Exception as e:
        logger.error(f"Error uploading image to MAX Bot API: {e}")
    return None


async def send_max_bot_message(
    token: str,
    recipient: str,
    text: str,
    format: str = "markdown",
    notify: bool = True,
    buttons: Optional[List[List[Dict[str, Any]]]] = None,
    base_url: str = DEFAULT_MAX_BASE_URL,
    image_path: Optional[str] = None,
    image_url: Optional[str] = None
) -> Dict[str, Any]:
    """
    Отправка сообщения через официальный Bot API MAX.
    Recipient может быть user_id или chat_id.
    """
    clean_rec = str(recipient).strip()
    is_chat = clean_rec.startswith("chat_") or clean_rec.startswith("-") or clean_rec.startswith("c:")
    
    if is_chat:
        chat_val = clean_rec.replace("chat_", "").replace("c:", "")
        url = f"{base_url.rstrip('/')}/messages?chat_id={chat_val}"
    else:
        url = f"{base_url.rstrip('/')}/messages?user_id={clean_rec}"

    headers = {
        "Authorization": token.strip(),
        "Content-Type": "application/json"
    }

    body: Dict[str, Any] = {
        "text": text,
        "format": format,
        "notify": notify
    }

    attachments: List[Dict[str, Any]] = []
    if image_path:
        up_att = await upload_max_bot_image(token, image_path, base_url)
        if up_att:
            attachments.append(up_att)
        elif image_url:
            attachments.append({"type": "image", "payload": {"url": image_url}})
    elif image_url:
        attachments.append({"type": "image", "payload": {"url": image_url}})

    if buttons and len(buttons) > 0:
        attachments.append({
            "type": "inline_keyboard",
            "payload": {
                "buttons": buttons
            }
        })
    if attachments:
        body["attachments"] = attachments

    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.post(url, headers=headers, json=body)
            if resp.status_code in [200, 201]:
                res_data = resp.json()
                msg_id = ""
                if isinstance(res_data, dict):
                    msg_obj = res_data.get("message") or res_data
                    msg_id = str(msg_obj.get("id") or msg_obj.get("body", {}).get("mid") or "")
                return {"success": True, "msg_id": msg_id, "data": res_data}
            else:
                logger.warning(f"Ошибка отправки через Bot API MAX ({resp.status_code}): {resp.text}")
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        logger.error(f"Исключение при отправке сообщения через Bot API MAX: {e}")
        return {"success": False, "error": str(e)}


class MaxSendResult(dict):
    """Словарь с результатом отправки, приводящийся к bool(success) для обратной совместимости"""
    def __bool__(self):
        return bool(self.get("success", False))


async def send_max_message(
    recipient: Optional[str] = None,
    text: str = "",
    session: Optional[Any] = None,
    settings: Optional[MaxSettings] = None,
    phone: Optional[str] = None,
    format: str = "markdown",
    notify: bool = True,
    buttons: Optional[List[List[Dict[str, Any]]]] = None,
    prefer_channel: Optional[str] = None,
    bot_id: Optional[int] = None,
    image_path: Optional[str] = None,
    image_url: Optional[str] = None,
    **kwargs
) -> MaxSendResult:
    """
    Интеллектуальный маршрутизатор отправки сообщений MAX:
    1. Проверяет глобальные настройки MAX и наличие ботов.
    2. Позволяет выбрать конкретного бота (bot_id) или бота по умолчанию.
    3. Поддерживает режимы:
       - 'cascade' (по умолчанию): сначала бот, при неудаче фоллбэк на личный аккаунт Web Bridge.
       - 'bot_only': строго выбранный бот MAX.
       - 'bridge_only': строго отправка из личного аккаунта Web Bridge по номеру телефона.
    4. Записывает событие в MaxMessageLog.
    """
    target_param = recipient or phone or kwargs.get("target") or ""
    if not target_param:
        return MaxSendResult({"success": False, "error": "Не указан получатель (recipient / phone)"})

    from app.core.database import engine
    
    if isinstance(session, MaxSettings):
        settings = session
        session = None

    if session is not None:
        return await _do_send_max_message(
            clean_target=str(target_param).strip(),
            text=text,
            db=session,
            settings=settings,
            format=format,
            notify=notify,
            buttons=buttons,
            prefer_channel=prefer_channel,
            bot_id=bot_id,
            image_path=image_path or kwargs.get("image_path"),
            image_url=image_url or kwargs.get("image_url")
        )
    else:
        with Session(engine) as db:
            return await _do_send_max_message(
                clean_target=str(target_param).strip(),
                text=text,
                db=db,
                settings=settings,
                format=format,
                notify=notify,
                buttons=buttons,
                prefer_channel=prefer_channel,
                bot_id=bot_id,
                image_path=image_path or kwargs.get("image_path"),
                image_url=image_url or kwargs.get("image_url")
            )


async def _do_send_max_message(
    clean_target: str,
    text: str,
    db: Session,
    settings: Optional[MaxSettings] = None,
    format: str = "markdown",
    notify: bool = True,
    buttons: Optional[List[List[Dict[str, Any]]]] = None,
    prefer_channel: Optional[str] = None,
    bot_id: Optional[int] = None,
    image_path: Optional[str] = None,
    image_url: Optional[str] = None
) -> MaxSendResult:
    if not settings:
        settings = db.exec(select(MaxSettings)).first()
    if not settings or not settings.is_active:
        return MaxSendResult({"success": False, "error": "Интеграция с мессенджером MAX отключена в настройках"})

    customer_id: Optional[int] = None
    target_user_id: Optional[str] = None
    phone_number: Optional[str] = None

    # Проверяем, является ли получатель номером телефона
    digits = "".join(filter(str.isdigit, clean_target))
    if len(digits) >= 10 and not clean_target.startswith("chat_") and not clean_target.startswith("-"):
        phone_number = _clean_phone_number(digits)
        # Ищем клиента в CRM
        customer = db.exec(select(Customer).where(Customer.phone.like(f"%{phone_number[-10:]}%"))).first()
        if customer:
            customer_id = customer.id
            target_user_id = customer.max_user_id

        # Если max_user_id еще нет, пробуем найти через Web Bridge
        if not target_user_id and (settings.auto_search_phone or prefer_channel in ["auto", "cascade", "bot_first"] or len(digits) >= 10):
            try:
                search_res = await max_bridge_service.search_user_by_phone(phone_number, db)
                if search_res.get("found") and search_res.get("user_id"):
                    target_user_id = search_res.get("user_id")
            except Exception as se:
                logger.debug(f"Search user by phone note: {se}")
    else:
        # Прямой user_id или chat_id
        target_user_id = clean_target
        # Пробуем найти клиента в CRM по max_user_id
        customer = db.exec(select(Customer).where(Customer.max_user_id == clean_target)).first()
        if customer:
            customer_id = customer.id
            if customer.phone:
                phone_number = _clean_phone_number(customer.phone)

    # Выбор бота: если передан bot_id, ищем его, иначе берем дефолтного или первого активного
    selected_bot = None
    if bot_id:
        selected_bot = db.get(MaxBot, bot_id)
        if not selected_bot or not selected_bot.is_active:
            logger.warning(f"Выбранный бот MAX #{bot_id} не найден или не активен, ищем резервного")
            selected_bot = None

    if not selected_bot:
        selected_bot = db.exec(
            select(MaxBot)
            .where(MaxBot.is_active == True)
            .where(MaxBot.is_default_for_notifications == True)
        ).first()
    if not selected_bot:
        selected_bot = db.exec(select(MaxBot).where(MaxBot.is_active == True)).first()

    base_url = (settings.base_url or DEFAULT_MAX_BASE_URL).rstrip('/')
    send_mode = (prefer_channel or settings.send_priority or "cascade").lower()

    log_entry = MaxMessageLog(
        recipient=clean_target,
        customer_id=customer_id,
        channel_type="bot" if send_mode not in ["bridge_only", "bridge", "bridge_first"] else "bridge",
        bot_id=selected_bot.id if selected_bot else None,
        text=text,
        format=format,
        notify=notify,
        buttons_json=json.dumps(buttons) if buttons else None,
        status="pending"
    )

    result = {"success": False, "error": "Нет доступных каналов отправки MAX"}

    # ==============================================================
    # РЕЖИМ 1: bridge_only (Строго личный аккаунт Web Bridge по номеру телефона)
    # ==============================================================
    if send_mode in ["bridge_only", "bridge", "bridge_first"]:
        target_peer = phone_number or target_user_id or clean_target
        try:
            bridge_res = await max_bridge_service.send_bridge_message(peer_id=target_peer, text=text, db=db)
            result = {"success": True, "msg_id": bridge_res.get("msg_id"), "via": "bridge"}
            log_entry.status = "sent"
            log_entry.channel_type = "bridge"
            log_entry.max_message_id = str(bridge_res.get("msg_id") or "")
        except Exception as be:
            log_entry.status = "failed"
            log_entry.error_text = f"Ошибка отправки через личный аккаунт MAX: {be}"
            result = {"success": False, "error": log_entry.error_text}

    # ==============================================================
    # РЕЖИМ 2: bot_only (Строго выбранный бот MAX, без фоллбэка на личный)
    # ==============================================================
    elif send_mode in ["bot_only", "bot"]:
        if not selected_bot:
            result = {"success": False, "error": "Активный бот MAX не настроен для отправки"}
            log_entry.status = "failed"
            log_entry.error_text = result["error"]
        elif not target_user_id:
            result = {
                "success": False, 
                "error": "Получатель не запустил бота MAX (нет MAX ID). Отправка от личного аккаунта отключена (режим 'Только бот')."
            }
            log_entry.status = "failed"
            log_entry.error_text = result["error"]
        else:
            bot_res = await send_max_bot_message(
                token=selected_bot.bot_token,
                recipient=target_user_id,
                text=text,
                format=format,
                notify=notify,
                buttons=buttons,
                base_url=base_url,
                image_path=image_path,
                image_url=image_url
            )
            if bot_res.get("success"):
                result = bot_res
                result["via"] = "bot"
                log_entry.status = "sent"
                log_entry.channel_type = "bot"
                log_entry.max_message_id = str(bot_res.get("msg_id") or "")
            else:
                result = bot_res
                log_entry.status = "failed"
                log_entry.error_text = bot_res.get("error")

    # ==============================================================
    # РЕЖИМ 3: cascade / bot_first / auto (Каскад: Бот MAX ➔ Личный аккаунт)
    # ==============================================================
    else:
        bot_sent = False
        bot_err = None
        
        # 1. Сначала пробуем выбранного бота, если он есть и есть target_user_id
        if selected_bot and target_user_id:
            bot_res = await send_max_bot_message(
                token=selected_bot.bot_token,
                recipient=target_user_id,
                text=text,
                format=format,
                notify=notify,
                buttons=buttons,
                base_url=base_url,
                image_path=image_path,
                image_url=image_url
            )
            if bot_res.get("success"):
                bot_sent = True
                result = bot_res
                result["via"] = "bot"
                log_entry.status = "sent"
                log_entry.channel_type = "bot"
                log_entry.max_message_id = str(bot_res.get("msg_id") or "")
            else:
                bot_err = bot_res.get("error")
                logger.info(f"Бот MAX {selected_bot.bot_name} не смог доставить ({bot_err}), запускаем каскадный фоллбэк на личный аккаунт")
        elif not selected_bot:
            bot_err = "Бот MAX не настроен"
        else:
            bot_err = "У получателя нет MAX user_id (не нажимал старт в боте)"

        # 2. Если бот не смог доставить — каскадный переход на личный аккаунт Web Bridge
        if not bot_sent:
            target_bridge = phone_number or target_user_id or clean_target
            try:
                bridge_res = await max_bridge_service.send_bridge_message(peer_id=target_bridge, text=text, db=db, image_path=image_path, image_url=image_url)
                result = {"success": True, "msg_id": bridge_res.get("msg_id"), "via": "bridge_fallback"}
                log_entry.status = "sent"
                log_entry.channel_type = "bridge"
                log_entry.max_message_id = str(bridge_res.get("msg_id") or "")
            except Exception as be:
                log_entry.status = "failed"
                log_entry.error_text = f"Бот MAX: {bot_err}; Личный аккаунт: {be}"
                result = {"success": False, "error": log_entry.error_text}

    # Сохраняем в лог
    try:
        db.add(log_entry)
        db.commit()
    except Exception as le_err:
        logger.error(f"Не удалось записать лог отправки MAX: {le_err}")

    return MaxSendResult(result)



async def edit_max_message(
    message_id: str,
    recipient: str,
    text: str,
    buttons: Optional[List[List[Dict[str, Any]]]] = None,
    keep_image: bool = False,
    session: Optional[Session] = None,
    bot_id: Optional[int] = None
) -> Dict[str, Any]:
    """
    Редактирование ранее отправленного сообщения в MAX.
    Для Bot API: PUT /messages?message_id={message_id}
    При keep_image=False и buttons=[] в attachments передается [], что удаляет картинку QR и кнопки!
    """
    # 1. Если сообщение от Web Bridge
    if str(message_id).startswith("bridge_") or str(message_id).startswith("max_"):
        return {"success": True, "edited_bridge": True}

    from app.core.database import engine
    from app.models.max_settings import MaxBot, MaxSettings

    def _get_token(s: Session) -> Optional[str]:
        if bot_id:
            b = s.get(MaxBot, bot_id)
            if b and b.bot_token:
                return b.bot_token
        b_def = s.exec(select(MaxBot).where(MaxBot.is_active == True)).first()
        if b_def and b_def.bot_token:
            return b_def.bot_token
        settings = s.exec(select(MaxSettings)).first()
        return settings.api_key if settings else None

    token = None
    if session:
        token = _get_token(session)
    else:
        with Session(engine) as db:
            token = _get_token(db)

    if not token:
        return {"success": False, "error": "No MAX bot token"}

    url = f"{DEFAULT_MAX_BASE_URL.rstrip('/')}/messages?message_id={message_id}"
    headers = {
        "Authorization": token.strip(),
        "Content-Type": "application/json"
    }
    attachments: List[Dict[str, Any]] = []
    if buttons and len(buttons) > 0:
        attachments.append({
            "type": "inline_keyboard",
            "payload": {
                "buttons": buttons
            }
        })

    body = {
        "text": text,
        "format": "markdown",
        "attachments": attachments
    }
    try:
        async with httpx.AsyncClient(timeout=10.0, verify=False) as client:
            resp = await client.put(url, headers=headers, json=body)
            if resp.status_code in [200, 204]:
                return {"success": True, "data": resp.json() if resp.status_code == 200 else {}}
            else:
                return {"success": False, "error": f"HTTP {resp.status_code}: {resp.text}"}
    except Exception as e:
        logger.error(f"Error editing MAX message {message_id}: {e}")
        return {"success": False, "error": str(e)}
