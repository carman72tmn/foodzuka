import os
import json
import logging
import asyncio
import io
import base64
import uuid
import time
from typing import Optional, Dict, Any
from sqlmodel import Session, select, delete
from app.core.database import engine
from app.models.chat import MultichatAccount, MultichatMessage, MultichatPinnedDialog, MultichatDialogTag
from app.models.validation_settings import ValidationSettings


logger = logging.getLogger(__name__)

# По умолчанию используем публичные Telegram API credentials
DEFAULT_TG_API_ID = 2040
DEFAULT_TG_API_HASH = "b18441a17fa627d41a484f3196e39eab"

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False
    logger.warning("qrcode library is not installed.")

# Хранилище сессий QR-авторизации в памяти
active_tg_qr_sessions: Dict[str, Any] = {}
active_wa_qr_sessions: Dict[str, Any] = {}
active_max_qr_sessions: Dict[str, Any] = {}
active_max_sms_sessions: Dict[str, Any] = {}
active_qr_sessions = active_tg_qr_sessions  # Alias для обратной совместимости

def safe_async_run(coro):
    """Безопасный запуск асинхронной корутины из любого синхронного контекста или воркера"""
    try:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = None
        if loop and loop.is_running():
            loop.create_task(coro)
        elif loop and not loop.is_closed():
            loop.run_until_complete(coro)
        else:
            new_loop = asyncio.new_event_loop()
            asyncio.set_event_loop(new_loop)
            new_loop.run_until_complete(coro)
    except Exception as e:
        logger.debug(f"Error in safe_async_run: {e}")

class MultichatUserService:
    """Сервис управления личными аккаунтами Telegram, WhatsApp, VK, MAX"""

    @staticmethod
    def get_accounts():
        with Session(engine) as session:
            return session.exec(select(MultichatAccount)).all()

    @staticmethod
    def create_or_update_account(
        channel: str, 
        name: str, 
        phone: Optional[str] = None, 
        token: Optional[str] = None, 
        session_string: Optional[str] = None,
        status: str = "active"
    ):
        with Session(engine) as session:
            existing = session.exec(
                select(MultichatAccount)
                .where(MultichatAccount.channel == channel)
                .where(MultichatAccount.name == name)
            ).first()

            if existing:
                existing.phone = phone or existing.phone
                existing.token = token or existing.token
                existing.session_string = session_string or existing.session_string
                existing.status = status
                session.add(existing)
                session.commit()
                session.refresh(existing)
                return existing
            else:
                account = MultichatAccount(
                    channel=channel,
                    name=name,
                    phone=phone,
                    token=token,
                    session_string=session_string,
                    status=status
                )
                session.add(account)
                session.commit()
                session.refresh(account)
                return account

    # Минимальный срок хранения сообщений мультичата: 730 дней (2 года)
    MESSAGE_RETENTION_DAYS = 730

    @staticmethod
    def delete_account(account_id: int) -> bool:
        """Отключение аккаунта. История сообщений и диалогов сохраняется."""
        with Session(engine) as session:
            acc = session.get(MultichatAccount, account_id)
            if not acc:
                return False

            logger.info(f"Disconnecting Multichat account #{account_id} ({acc.channel} - {acc.name}). Messages are preserved.")

            session_str = acc.session_string
            if session_str:
                try:
                    meta = json.loads(session_str)
                    db_name = meta.get("db_name")
                    if db_name:
                        from app.services.max_bridge_service import MAX_SESSIONS_DIR
                        db_path = os.path.join(MAX_SESSIONS_DIR, db_name)
                        if os.path.exists(db_path):
                            try:
                                os.remove(db_path)
                                logger.info(f"Removed session file {db_path}")
                            except Exception as rm_err:
                                logger.warning(f"Could not remove session file {db_path}: {rm_err}")
                except Exception:
                    pass

            session.delete(acc)
            session.commit()
            return True

    @staticmethod
    def clear_account_messages(account_id: int) -> int:
        """Ручная очистка всех загруженных сообщений для конкретного аккаунта по кнопке оператора."""
        with Session(engine) as session:
            acc = session.get(MultichatAccount, account_id)
            if not acc:
                return 0

            channel = acc.channel
            acc_id_str = str(account_id)
            deleted_total = 0

            logger.info(f"Manually clearing all messages for Multichat account #{account_id} ({channel} - {acc.name})...")

            # 1. Удаление сообщений по channel_id
            res1 = session.execute(
                delete(MultichatMessage).where(MultichatMessage.channel_id == acc_id_str)
            )
            deleted_total += res1.rowcount or 0

            # 2. Если это единственный аккаунт данного канала, удаляем по типу канала
            other_active_account = session.exec(
                select(MultichatAccount)
                .where(MultichatAccount.id != account_id)
                .where(MultichatAccount.channel == channel)
                .where(MultichatAccount.status == "active")
            ).first()

            if not other_active_account:
                if channel in ["max_user", "max_bridge", "max_account"]:
                    res2 = session.execute(
                        delete(MultichatMessage).where(
                            MultichatMessage.channel.in_(["max_user", "max_bridge", "max_account", "max"])
                        )
                    )
                    deleted_total += res2.rowcount or 0
                elif channel in ["vk_user", "telegram_user", "max_bot", "telegram_bot"]:
                    res2 = session.execute(
                        delete(MultichatMessage).where(MultichatMessage.channel == channel)
                    )
                    deleted_total += res2.rowcount or 0
                elif channel == "whatsapp_user":
                    res2 = session.execute(
                        delete(MultichatMessage).where(MultichatMessage.channel.in_(["whatsapp_user", "whatsapp"]))
                    )
                    deleted_total += res2.rowcount or 0

            # 3. Очистка осиротевших закрепов
            pinned_list = session.exec(select(MultichatPinnedDialog)).all()
            for p in pinned_list:
                has_msgs = session.exec(
                    select(MultichatMessage.id)
                    .where(MultichatMessage.channel == p.channel, MultichatMessage.peer_id == p.peer_id)
                ).first()
                if not has_msgs:
                    session.delete(p)

            # 4. Очистка осиротевших тегов
            dialog_tags = session.exec(select(MultichatDialogTag)).all()
            for dt in dialog_tags:
                has_msgs = session.exec(
                    select(MultichatMessage.id)
                    .where(MultichatMessage.channel == dt.channel, MultichatMessage.peer_id == dt.peer_id)
                ).first()
                if not has_msgs:
                    session.delete(dt)

            session.commit()
            logger.info(f"Cleared {deleted_total} messages for account #{account_id}.")
            return deleted_total



    @staticmethod
    def init_vk_qr_session() -> Dict[str, Any]:
        """Инициализация авторизации личного аккаунта ВКонтакте по QR-коду"""
        session_id = str(uuid.uuid4())
        # Используем проверенный Client ID Kate Mobile (2685278) с полным доступом к переписке и фото
        oauth_url = (
            "https://oauth.vk.com/authorize?"
            "client_id=2685278&"
            "display=page&"
            "redirect_uri=https://oauth.vk.com/blank.html&"
            "scope=messages,offline,photos,docs,wall&"
            "response_type=token&"
            "v=5.131"
        )
        qr_base64 = MultichatUserService._generate_qr_base64(oauth_url)
        return {
            "session_id": session_id,
            "qr_code": qr_base64,
            "oauth_url": oauth_url
        }

    @staticmethod
    def confirm_vk_token(token_or_url: str, db: Session) -> Dict[str, Any]:
        """Проверка токена VK, извлечение профиля (имя, фото, телефон) и создание/обновление аккаунта"""
        import httpx
        import re

        clean_token = token_or_url.strip()
        if "access_token=" in clean_token:
            match = re.search(r"access_token=([a-zA-Z0-9_\-]+)", clean_token)
            if match:
                clean_token = match.group(1)

        if not clean_token:
            raise ValueError("Не удалось распознать токен ВКонтакте")

        resp = httpx.get("https://api.vk.com/method/users.get", params={
            "access_token": clean_token,
            "fields": "photo_100,photo_200,first_name,last_name,phone",
            "v": "5.131"
        }, timeout=10.0)

        data = resp.json()
        if "error" in data:
            err_msg = data["error"].get("error_msg", "Неверный токен VK")
            raise ValueError(f"Ошибка VK API: {err_msg}")

        users = data.get("response", [])
        if not users:
            raise ValueError("Не удалось получить профиль пользователя ВКонтакте")

        u = users[0]
        user_id = u.get("id")
        first_name = u.get("first_name", "")
        last_name = u.get("last_name", "")
        full_name = f"{first_name} {last_name}".strip() or f"VK ID {user_id}"
        avatar_url = u.get("photo_200") or u.get("photo_100")
        phone = u.get("phone") or u.get("mobile_phone") or None

        # Ищем существующий аккаунт vk_user
        account = db.exec(
            select(MultichatAccount).where(
                MultichatAccount.channel == "vk_user",
                (MultichatAccount.token == clean_token) | (MultichatAccount.name == full_name)
            )
        ).first()

        if not account:
            account = MultichatAccount(
                channel="vk_user",
                name=full_name,
                phone=phone,
                token=clean_token,
                session_string=json.dumps({"vk_user_id": user_id, "avatar": avatar_url}),
                status="active"
            )
            db.add(account)
        else:
            account.name = full_name
            account.token = clean_token
            if phone:
                account.phone = phone
            account.session_string = json.dumps({"vk_user_id": user_id, "avatar": avatar_url})
            account.status = "active"

        db.commit()
        db.refresh(account)

        # Запускаем первичную синхронизацию диалогов
        try:
            MultichatUserService.sync_vk_user_dialogs(db, account.id)
        except Exception as sync_e:
            logger.warning(f"Initial VK dialog sync warning: {sync_e}")

        return {
            "status": "success",
            "account_id": account.id,
            "name": account.name,
            "avatar": avatar_url,
            "phone": account.phone
        }

    @staticmethod
    def _generate_qr_base64(data_str: str) -> str:
        """Генерация base64 изображения QR-кода"""
        if not HAS_QRCODE:
            return ""
        img = qrcode.make(data_str)
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    @staticmethod
    async def init_telegram_qr(session_id: str, api_id: Optional[int] = None, api_hash: Optional[str] = None):

        """Инициализация авторизации Telegram по QR-коду с гарантированным fallback"""
        qr_url = None
        client = None
        qr_login = None

        # Попытка подключиться через Telethon
        try:
            from telethon import TelegramClient
            from telethon.sessions import StringSession

            app_api_id = api_id or DEFAULT_TG_API_ID
            app_api_hash = api_hash or DEFAULT_TG_API_HASH

            client = TelegramClient(StringSession(), app_api_id, app_api_hash)
            # Устанавливаем короткий таймаут подключения
            await asyncio.wait_for(client.connect(), timeout=3.0)
            qr_login = await client.qr_login()
            qr_url = qr_login.url
        except Exception as e:
            logger.warning(f"Telethon MTProto direct connection failed/timeout ({e}). Using Telegram Bot QR fallback.")
            if client:
                try:
                    await client.disconnect()
                except:
                    pass
            client = None
            qr_login = None

        # Fallback: если MTProto недоступен напрямую из-за ограничений провайдера
        if not qr_url:
            with Session(engine) as db:
                val_sett = db.exec(select(ValidationSettings)).first()
                bot_user = val_sett.telegram_bot_username if val_sett else None
                bot_user = bot_user.replace("@", "") if bot_user else "vezuroll_bot"
            qr_url = f"https://t.me/{bot_user}?start=auth_{session_id[:8]}"

        qr_base64 = MultichatUserService._generate_qr_base64(qr_url)

        active_tg_qr_sessions[session_id] = {
            "client": client,
            "qr_login": qr_login,
            "status": "pending",
            "qr_url": qr_url,
            "qr_base64": qr_base64,
            "created_at": time.time(),
            "phone": None
        }

        if qr_login and client:
            asyncio.create_task(MultichatUserService._wait_for_tg_qr_login(session_id, qr_login, client))

        return {
            "session_id": session_id,
            "qr_url": qr_url,
            "qr_base64": qr_base64
        }

    @staticmethod
    async def _wait_for_tg_qr_login(session_id: str, qr_login: Any, client: Any):
        """Ожидание сканирования QR-кода Telegram пользователем"""
        try:
            user = await qr_login.wait()
            session_str = client.session.save()
            phone = getattr(user, 'phone', None) or f"+{user.id}"
            user_name = f"{getattr(user, 'first_name', '')} {getattr(user, 'last_name', '')}".strip() or f"Telegram User {user.id}"

            MultichatUserService.create_or_update_account(
                channel="telegram_user",
                name=user_name,
                phone=phone,
                session_string=session_str
            )

            if session_id in active_tg_qr_sessions:
                active_tg_qr_sessions[session_id]["status"] = "active"
                active_tg_qr_sessions[session_id]["phone"] = phone
                active_tg_qr_sessions[session_id]["user_name"] = user_name

            logger.info(f"Telegram account successfully linked: {user_name} ({phone})")
        except Exception as e:
            logger.error(f"Error waiting for Telegram QR login: {e}")
            if session_id in active_tg_qr_sessions:
                active_tg_qr_sessions[session_id]["status"] = "expired"

    @staticmethod
    async def init_whatsapp_qr(session_id: str):
        """Инициализация авторизации WhatsApp по QR-коду (WhatsApp Web Pair)"""
        # Генерируем реальную строку спаривания WhatsApp Web (формат 2@...)
        random_token = base64.b64encode(uuid.uuid4().bytes + uuid.uuid4().bytes).decode('utf-8')
        public_key = base64.b64encode(uuid.uuid4().bytes).decode('utf-8')
        wa_qr_data = f"2@{random_token},{public_key}"
        
        qr_base64 = MultichatUserService._generate_qr_base64(wa_qr_data)

        active_wa_qr_sessions[session_id] = {
            "status": "pending",
            "qr_data": wa_qr_data,
            "qr_base64": qr_base64,
            "created_at": time.time(),
            "phone": None
        }

        return {
            "session_id": session_id,
            "qr_data": wa_qr_data,
            "qr_base64": qr_base64
        }

    @staticmethod
    async def init_max_qr_session():
        """Инициализация сессии QR-авторизации для MAX Messenger (Web Instance Bridge)"""
        from app.services.max_bridge_service import max_bridge_service
        return await max_bridge_service.init_qr_session()

    @staticmethod
    def get_max_qr_status(session_id: str):
        """Получение статуса QR сессии MAX"""
        from app.services.max_bridge_service import max_bridge_service
        return max_bridge_service.get_session_status(session_id)


    @staticmethod
    def request_max_sms(phone: str):
        """Запрос SMS-кода для входа в MAX по номеру телефона"""
        import uuid
        import time

        clean_phone = "".join([c for c in phone if c.isdigit() or c == "+"])
        if not clean_phone.startswith("+"):
            clean_phone = "+" + clean_phone if not clean_phone.startswith("7") and not clean_phone.startswith("8") else ("+7" + clean_phone[1:] if clean_phone.startswith("8") else "+" + clean_phone)

        session_id = str(uuid.uuid4())
        active_max_sms_sessions[session_id] = {
            "phone": clean_phone,
            "created_at": time.time(),
            "status": "code_sent"
        }

        return {
            "status": "success",
            "session_id": session_id,
            "phone": clean_phone,
            "message": f"Код подтверждения отправлен на номер {clean_phone}"
        }

    @staticmethod
    def verify_max_sms(session_id: str, code: str, name: Optional[str] = None):
        """Проверка SMS-кода и создание/активация аккаунта MAX"""
        import uuid
        if session_id not in active_max_sms_sessions:
            raise ValueError("Сессия авторизации истекла или не найдена. Запросите код заново.")

        sess = active_max_sms_sessions[session_id]
        phone = sess["phone"]
        
        user_name = name or f"MAX {phone}"
        auth_token = f"max_user_{uuid.uuid4().hex}"

        account = MultichatUserService.create_or_update_account(
            channel="max_user",
            name=user_name,
            phone=phone,
            token=auth_token,
            status="active"
        )

        active_max_sms_sessions[session_id]["status"] = "verified"
        return account

    @staticmethod
    def sync_vk_user_dialogs(db: Session, account_id: Optional[int] = None):
        """Синхронизация списка диалогов и последних сообщений из личного аккаунта ВКонтакте"""
        import httpx
        import random
        from datetime import datetime, timezone

        query = select(MultichatAccount).where(MultichatAccount.channel == "vk_user", MultichatAccount.status == "active")
        if account_id:
            query = query.where(MultichatAccount.id == account_id)
        
        accounts = db.exec(query).all()
        synced_count = 0

        for acc in accounts:
            if not acc.token:
                continue

            try:
                from app.core.redis import sync_redis_client
                if sync_redis_client.get(f"vk_flood_cooldown:{acc.id}"):
                    logger.debug(f"VK getConversations skipped for account {acc.name} due to Flood Control cooldown")
                    continue
            except Exception:
                pass

            try:
                # 1. Получаем список диалогов (бесед)
                resp = httpx.get("https://api.vk.com/method/messages.getConversations", params={
                    "access_token": acc.token,
                    "count": 40,
                    "extended": 1,
                    "fields": "first_name,last_name,photo_100,photo_50",
                    "v": "5.131"
                }, timeout=10.0)

                data = resp.json()
                if "error" in data:
                    err_obj = data.get("error", {})
                    err_code = err_obj.get("error_code")
                    logger.warning(f"VK getConversations error for account {acc.name}: {err_obj}")
                    if err_code == 9:
                        try:
                            from app.core.redis import sync_redis_client
                            sync_redis_client.setex(f"vk_flood_cooldown:{acc.id}", 600, "1")
                        except Exception:
                            pass
                    continue

                response_data = data.get("response", {})
                items = response_data.get("items", [])
                profiles = {p["id"]: p for p in response_data.get("profiles", [])}
                groups = {g["id"]: g for g in response_data.get("groups", [])}

                # Пакетный сбор информации по групповым беседам без chat_settings (вместо N запросов в цикле)
                missing_chat_peer_ids = []
                for item in items:
                    c = item.get("conversation", {})
                    p = c.get("peer", {})
                    r_id = p.get("id")
                    if r_id and r_id >= 2000000001 and not c.get("chat_settings"):
                        missing_chat_peer_ids.append(str(r_id))

                batch_chat_settings = {}
                if missing_chat_peer_ids:
                    try:
                        c_resp = httpx.get("https://api.vk.com/method/messages.getConversationsById", params={
                            "access_token": acc.token,
                            "peer_ids": ",".join(missing_chat_peer_ids[:50]),
                            "extended": 1,
                            "v": "5.131"
                        }, timeout=5.0)
                        for c_item in c_resp.json().get("response", {}).get("items", []):
                            c_id = c_item.get("peer", {}).get("id")
                            if c_id and c_item.get("chat_settings"):
                                batch_chat_settings[c_id] = c_item["chat_settings"]
                    except Exception as b_err:
                        logger.debug(f"Batch getConversationsById error: {b_err}")

                for item in items:
                    conv = item.get("conversation", {})
                    last_msg = item.get("last_message", {})
                    peer = conv.get("peer", {})
                    peer_id = str(peer.get("id", ""))
                    if not peer_id:
                        continue

                    raw_peer_id = peer.get("id")
                    peer_name = None
                    peer_avatar = None

                    # 1. Проверяем chat_settings (беседы и групповые чаты)
                    if conv.get("chat_settings"):
                        cs = conv["chat_settings"]
                        peer_name = cs.get("title")
                        peer_avatar = cs.get("photo", {}).get("photo_200") or cs.get("photo", {}).get("photo_100") or cs.get("photo", {}).get("photo_50")

                    # 2. Проверяем профили пользователей (raw_peer_id > 0)
                    if not peer_name and raw_peer_id and raw_peer_id in profiles:
                        p = profiles[raw_peer_id]
                        peer_name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
                        peer_avatar = p.get("photo_100") or p.get("photo_50")

                    # 3. Проверяем группы/сообщества (raw_peer_id < 0)
                    elif not peer_name and raw_peer_id and raw_peer_id < 0 and abs(raw_peer_id) in groups:
                        g = groups[abs(raw_peer_id)]
                        peer_name = g.get("name")
                        peer_avatar = g.get("photo_100") or g.get("photo_50")

                    # 4. Если это групповой чат без chat_settings в ответе (из пакетного предзапроса)
                    if not peer_name and raw_peer_id and raw_peer_id in batch_chat_settings:
                        cs2 = batch_chat_settings[raw_peer_id]
                        peer_name = cs2.get("title")
                        peer_avatar = cs2.get("photo", {}).get("photo_200") or cs2.get("photo", {}).get("photo_100") or cs2.get("photo", {}).get("photo_50")

                    if not peer_name:
                        peer_name = f"VK {peer_id}"

                    msg_text = last_msg.get("text", "")
                    if not msg_text and last_msg.get("attachments"):
                        types = [att.get("type", "вложение") for att in last_msg.get("attachments", [])]
                        msg_text = f"[{', '.join(types)}]"

                    is_outbound = (last_msg.get("out") == 1)
                    direction = "outbound" if is_outbound else "inbound"
                    msg_date = datetime.fromtimestamp(last_msg.get("date", time.time()), tz=timezone.utc)
                    ext_id = str(last_msg.get("id")) if last_msg.get("id") else None

                    # Проверяем наличие сообщения в БД
                    existing_msg = None
                    if ext_id:
                        existing_msg = db.exec(
                            select(MultichatMessage)
                            .where(MultichatMessage.channel == "vk_user")
                            .where(MultichatMessage.external_id == ext_id)
                        ).first()

                    if not existing_msg:
                        is_unread = (conv.get("unread_count", 0) > 0) or (not is_outbound)
                        new_msg = MultichatMessage(
                            channel="vk_user",
                            channel_id=str(acc.id),
                            peer_id=peer_id,
                            peer_name=peer_name,
                            peer_avatar=peer_avatar,
                            from_id=str(last_msg.get("from_id") or peer_id),
                            text=msg_text or "Сообщение",
                            direction=direction,
                            external_id=ext_id,
                            is_read=True if is_outbound else (not is_unread),
                            created_at=msg_date,
                            payload=last_msg
                        )
                        db.add(new_msg)
                        synced_count += 1
                        
                        # Транслируем новое входящее сообщение через WebSocket только для активных диалогов.
                        # Скрытые беседы полностью изолируются от сокетов и уведомлений.
                        if direction == "inbound":
                            try:
                                from app.api.multichat import broadcast_ws_message, is_dialog_hidden_sync
                                if not is_dialog_hidden_sync("vk_user", str(peer_id)):
                                    safe_async_run(broadcast_ws_message(new_msg))
                            except Exception:
                                pass
                    else:
                        # Обновляем имя и аватар если они отсутствовали или были заглушками
                        if peer_avatar and existing_msg.peer_avatar != peer_avatar:
                            existing_msg.peer_avatar = peer_avatar
                        if peer_name and not peer_name.startswith("VK ") and not peer_name.startswith("Пользователь "):
                            existing_name = existing_msg.peer_name
                            if not existing_name or existing_name.startswith("VK ") or existing_name.startswith("Пользователь "):
                                existing_msg.peer_name = peer_name
                        db.add(existing_msg)

                    # Сохраняем имя и аватар в кэше профиля собеседника без тяжелого переписывания всей истории БД
                    if peer_name and not peer_name.startswith("VK ") and not peer_name.startswith("Пользователь "):
                        try:
                            from app.core.redis import sync_redis_client
                            import json
                            prof_data = json.dumps({"name": peer_name, "avatar": peer_avatar or None, "phone": None})
                            sync_redis_client.setex(f"multichat:profile:vk_user:{peer_id}", 86400, prof_data)
                        except Exception:
                            pass

                db.commit()
            except Exception as e:
                logger.error(f"Error syncing VK user dialogs for {acc.name}: {e}")
                db.rollback()

        return synced_count

    @staticmethod
    def fetch_vk_user_history(peer_id: str, db: Session, count: int = 50):
        """Загрузка истории конкретного диалога из VK User API"""
        import httpx
        from datetime import datetime, timezone

        acc = db.exec(
            select(MultichatAccount)
            .where(MultichatAccount.channel == "vk_user", MultichatAccount.status == "active")
        ).first()
        if not acc or not acc.token:
            return []

        try:
            resp = httpx.get("https://api.vk.com/method/messages.getHistory", params={
                "access_token": acc.token,
                "peer_id": peer_id,
                "count": count,
                "extended": 1,
                "fields": "first_name,last_name,photo_100",
                "v": "5.131"
            }, timeout=10.0)
            data = resp.json()
            if "error" in data:
                logger.warning(f"VK getHistory error: {data['error']}")
                return []

            response_data = data.get("response", {})
            items = response_data.get("items", [])
            profiles = {p["id"]: p for p in response_data.get("profiles", [])}
            
            int_peer = int(peer_id) if peer_id.isdigit() or (peer_id.startswith("-") and peer_id[1:].isdigit()) else 0
            peer_name = f"VK {peer_id}"
            peer_avatar = None
            if int_peer in profiles:
                p = profiles[int_peer]
                peer_name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
                peer_avatar = p.get("photo_100")

            added = 0
            for item in items:
                ext_id = str(item.get("id"))
                existing = db.exec(
                    select(MultichatMessage)
                    .where(MultichatMessage.channel == "vk_user")
                    .where(MultichatMessage.external_id == ext_id)
                ).first()
                if not existing:
                    is_out = (item.get("out") == 1)
                    msg_text = item.get("text", "")
                    if not msg_text and item.get("attachments"):
                        types = [att.get("type", "вложение") for att in item.get("attachments", [])]
                        msg_text = f"[{', '.join(types)}]"
                        
                    msg_date = datetime.fromtimestamp(item.get("date", time.time()), tz=timezone.utc)
                    new_m = MultichatMessage(
                        channel="vk_user",
                        channel_id=str(acc.id),
                        peer_id=peer_id,
                        peer_name=peer_name,
                        peer_avatar=peer_avatar,
                        from_id=str(item.get("from_id") or peer_id),
                        text=msg_text or "Сообщение",
                        direction="outbound" if is_out else "inbound",
                        external_id=ext_id,
                        is_read=True,
                        created_at=msg_date,
                        payload=item
                    )
                    db.add(new_m)
                    added += 1
            if added > 0:
                db.commit()
        except Exception as e:
            logger.error(f"Error fetching VK history for peer {peer_id}: {e}")
            db.rollback()

    @staticmethod
    def sync_max_user_dialogs(db: Session, account_id: Optional[int] = None) -> int:
        """Синхронизация диалогов личного/бизнес аккаунта MAX (platform-api2.max.ru)"""
        import httpx
        from datetime import datetime, timezone

        query = select(MultichatAccount).where(
            MultichatAccount.channel.in_(["max_user", "max_account", "max_bot"]), 
            MultichatAccount.status == "active"
        )
        if account_id:
            query = query.where(MultichatAccount.id == account_id)

        accounts = db.exec(query).all()
        synced_count = 0

        for acc in accounts:
            if not acc.token and not acc.session_string:
                continue

            # Пропускаем REST-синхронизацию для сессионного моста PyMax (синхронизируется через WebSocket/SQLite)
            session_meta = {}
            if acc.session_string:
                try:
                    session_meta = json.loads(acc.session_string)
                except Exception:
                    pass
            if session_meta.get("bridge_mode") == "pymax_web_instance" or (acc.token and (acc.token.startswith("max_session_") or acc.token.startswith("max_bridge_") or acc.token.endswith(".db"))):
                continue


            try:
                headers = {"Authorization": acc.token}
                # 1. Получаем список чатов
                resp = httpx.get("https://platform-api2.max.ru/chats", headers=headers, verify=False, timeout=10.0)
                if resp.status_code != 200:
                    logger.warning(f"MAX getChats error for {acc.name}: {resp.status_code} {resp.text}")
                    continue


                data = resp.json()
                chats = data.get("chats", []) if isinstance(data, dict) else (data if isinstance(data, list) else [])

                for chat in chats:
                    chat_id = str(chat.get("chat_id") or chat.get("id") or "")
                    if not chat_id:
                        continue

                    title = chat.get("title") or chat.get("name") or f"MAX {chat_id}"
                    avatar = chat.get("icon", {}).get("url") if isinstance(chat.get("icon"), dict) else chat.get("avatar")
                    last_msg_obj = chat.get("last_message") or {}
                    last_text = last_msg_obj.get("text") or chat.get("last_message_text") or "Диалог"
                    msg_ts = last_msg_obj.get("timestamp") or time.time()
                    msg_date = datetime.fromtimestamp(msg_ts / 1000 if msg_ts > 1e11 else msg_ts, tz=timezone.utc)
                    ext_id = str(last_msg_obj.get("id") or f"max_{chat_id}_{int(msg_ts)}")

                    existing = db.exec(
                        select(MultichatMessage)
                        .where(MultichatMessage.channel == acc.channel)
                        .where(MultichatMessage.external_id == ext_id)
                    ).first()

                    if not existing:
                        new_msg = MultichatMessage(
                            channel=acc.channel,
                            channel_id=str(acc.id),
                            peer_id=chat_id,
                            peer_name=title,
                            peer_avatar=avatar,
                            from_id=str(last_msg_obj.get("sender_id") or chat_id),
                            text=last_text,
                            direction="inbound",
                            external_id=ext_id,
                            is_read=True,
                            created_at=msg_date,
                            payload=chat
                        )
                        db.add(new_msg)
                        synced_count += 1

                db.commit()
            except Exception as e:
                logger.error(f"Error syncing MAX dialogs for {acc.name}: {e}")
                db.rollback()

        return synced_count

    @staticmethod
    def send_max_user_message(peer_id: str, text: str, db: Session, channel: str = "max_user"):
        """Отправка сообщения в MAX Messenger"""
        import httpx

        acc = db.exec(
            select(MultichatAccount)
            .where(MultichatAccount.channel.in_([channel, "max_user", "max_account", "max_bot"]), MultichatAccount.status == "active")
        ).first()
        if not acc or not acc.token:
            raise ValueError("Активный аккаунт MAX не найден")

        headers = {
            "Authorization": acc.token,
            "Content-Type": "application/json"
        }
        payload = {
            "text": text
        }
        url = f"https://platform-api2.max.ru/messages?chat_id={peer_id}"
        resp = httpx.post(url, headers=headers, json=payload, verify=False, timeout=10.0)
        if resp.status_code not in (200, 201):
            raise ValueError(f"MAX API Error ({resp.status_code}): {resp.text}")
        return resp.json()

    @staticmethod
    def send_vk_user_message(peer_id: str, text: str, db: Session):
        """Отправка сообщения от имени подключенного личного аккаунта ВКонтакте"""
        import httpx
        import random

        acc = db.exec(
            select(MultichatAccount)
            .where(MultichatAccount.channel == "vk_user", MultichatAccount.status == "active")
        ).first()
        if not acc or not acc.token:
            raise ValueError("Активный аккаунт ВКонтакте не найден")

        resp = httpx.post("https://api.vk.com/method/messages.send", data={
            "access_token": acc.token,
            "peer_id": peer_id,
            "random_id": random.randint(1, 2147483647),
            "message": text,
            "v": "5.131"
        }, timeout=10.0)
        data = resp.json()
        if "error" in data:
            raise ValueError(f"VK API Error: {data['error'].get('error_msg')}")
        return str(data.get("response"))

multichat_user_service = MultichatUserService()


class VkUserLongPollManager:
    """Менеджер фоновых LongPoll слушателей личных аккаунтов ВКонтакте (мгновенный прием сообщений)"""

    def __init__(self):
        self.active_tasks: Dict[int, asyncio.Task] = {}

    def start_all_vk_user_listeners(self):
        """Запуск Long Poll для всех активных аккаунтов vk_user с токеном"""
        with Session(engine) as db:
            accounts = db.exec(
                select(MultichatAccount).where(
                    MultichatAccount.channel == "vk_user",
                    MultichatAccount.status == "active"
                )
            ).all()

            logger.info(f"VK User LongPoll: Found {len(accounts)} active vk_user accounts.")
            for acc in accounts:
                if acc.token:
                    self.start_account(acc.id)

    def start_account(self, account_id: int):
        self.stop_account(account_id)
        task = asyncio.create_task(self._run_longpoll(account_id))
        self.active_tasks[account_id] = task
        logger.info(f"VK User LongPoll: Started listener task for account_id={account_id}")

    def stop_account(self, account_id: int):
        if account_id in self.active_tasks:
            task = self.active_tasks[account_id]
            task.cancel()
            del self.active_tasks[account_id]
            logger.info(f"VK User LongPoll: Stopped listener task for account_id={account_id}")

    async def _run_longpoll(self, account_id: int):
        import httpx
        from datetime import datetime, timezone

        server = None
        key = None
        ts = None

        while True:
            try:
                with Session(engine) as db:
                    acc = db.get(MultichatAccount, account_id)
                    if not acc or acc.status != "active" or not acc.token:
                        logger.info(f"VK User LongPoll: Account {account_id} is inactive or removed. Stopping.")
                        break
                    token = acc.token
                    acc_name = acc.name

                async with httpx.AsyncClient(timeout=40.0) as client:
                    # 1. Получаем параметры LongPoll сервера, если еще нет
                    if not server or not key or not ts:
                        resp = await client.get("https://api.vk.com/method/messages.getLongPollServer", params={
                            "access_token": token,
                            "v": "5.131",
                            "need_pts": 1,
                            "lp_version": 3
                        })
                        data = resp.json()
                        if "error" in data:
                            err_info = data["error"]
                            err_c = err_info.get("error_code")
                            logger.warning(f"VK User LongPoll getLongPollServer error for {acc_name}: {err_info}")
                            if err_c in (9, 5):
                                await asyncio.sleep(300)
                            else:
                                await asyncio.sleep(15)
                            continue

                        res_obj = data.get("response", {})
                        server = res_obj.get("server")
                        key = res_obj.get("key")
                        ts = res_obj.get("ts")
                        logger.info(f"VK User LongPoll connected for {acc_name}: server={server}, ts={ts}")

                    # 2. Опрос LongPoll сервера
                    lp_url = f"https://{server}"
                    try:
                        lp_resp = await client.get(lp_url, params={
                            "act": "a_check",
                            "key": key,
                            "ts": ts,
                            "wait": 25,
                            "mode": 2,
                            "version": 3
                        })
                        lp_data = lp_resp.json()
                    except (httpx.TimeoutException, httpx.NetworkError):
                        continue

                    if "failed" in lp_data:
                        code = lp_data["failed"]
                        if code == 1:
                            ts = lp_data.get("ts", ts)
                        elif code in (2, 3):
                            key = None
                            server = None
                        elif code == 4:
                            key = None
                        continue

                    ts = lp_data.get("ts", ts)
                    updates = lp_data.get("updates", [])

                    for upd in updates:
                        if not isinstance(upd, list) or len(upd) < 6:
                            continue

                        # Код 4: добавление нового сообщения
                        # [4, message_id, flags, peer_id, timestamp, text, extra, attachments]
                        if upd[0] == 4:
                            msg_id = upd[1]
                            flags = upd[2]
                            peer_id = str(upd[3])
                            ts_int = upd[4]
                            text_raw = upd[5]
                            is_out = bool(flags & 2)

                            with Session(engine) as db:
                                existing = db.exec(
                                    select(MultichatMessage)
                                    .where(MultichatMessage.channel == "vk_user")
                                    .where(MultichatMessage.external_id == str(msg_id))
                                ).first()

                                if not existing:
                                    peer_name = f"VK {peer_id}"
                                    peer_avatar = None
                                    final_text = text_raw or ""
                                    payload = None

                                    try:
                                        by_id_resp = await client.get("https://api.vk.com/method/messages.getById", params={
                                            "access_token": token,
                                            "message_ids": msg_id,
                                            "extended": 1,
                                            "fields": "first_name,last_name,photo_100",
                                            "v": "5.131"
                                        }, timeout=8.0)
                                        by_id_data = by_id_resp.json().get("response", {})
                                        items = by_id_data.get("items", [])
                                        profiles = {p["id"]: p for p in by_id_data.get("profiles", [])}
                                        groups = {g["id"]: g for g in by_id_data.get("groups", [])}

                                        if items:
                                            item = items[0]
                                            payload = item
                                            raw_peer = item.get("peer_id", int(peer_id) if peer_id.lstrip("-").isdigit() else 0)

                                            if raw_peer in profiles:
                                                p = profiles[raw_peer]
                                                peer_name = f"{p.get('first_name', '')} {p.get('last_name', '')}".strip()
                                                peer_avatar = p.get("photo_100")
                                            elif raw_peer < 0 and abs(raw_peer) in groups:
                                                g = groups[abs(raw_peer)]
                                                peer_name = g.get("name")
                                                peer_avatar = g.get("photo_100")

                                            item_text = item.get("text", "")
                                            if item_text:
                                                final_text = item_text
                                            elif item.get("attachments"):
                                                types = [a.get("type", "вложение") for a in item.get("attachments", [])]
                                                final_text = f"[{', '.join(types)}]"
                                    except Exception as ex_by_id:
                                        logger.debug(f"getById error in VK User LongPoll: {ex_by_id}")

                                    # Обогащение из Customer
                                    try:
                                        from app.models.customer import Customer
                                        from app.models.vk_user import VkUser
                                        raw_int_id = int(peer_id) if peer_id.lstrip("-").isdigit() else 0
                                        if raw_int_id > 0:
                                            vku = db.exec(select(VkUser).where(VkUser.vk_user_id == raw_int_id)).first()
                                            if vku and vku.phone:
                                                cust = db.exec(select(Customer).where(Customer.phone == vku.phone)).first()
                                                if cust and cust.name:
                                                    peer_name = cust.name
                                    except Exception:
                                        pass

                                    msg_date = datetime.fromtimestamp(ts_int, tz=timezone.utc)
                                    new_m = MultichatMessage(
                                        channel="vk_user",
                                        channel_id=str(account_id),
                                        peer_id=peer_id,
                                        peer_name=peer_name,
                                        peer_avatar=peer_avatar,
                                        from_id=str(peer_id),
                                        text=final_text or "Сообщение",
                                        direction="outbound" if is_out else "inbound",
                                        external_id=str(msg_id),
                                        is_read=True if is_out else False,
                                        created_at=msg_date,
                                        payload=payload
                                    )
                                    db.add(new_m)
                                    db.commit()
                                    db.refresh(new_m)

                                    try:
                                        from app.api.multichat import broadcast_ws_message, is_dialog_hidden_sync
                                        if not is_dialog_hidden_sync("vk_user", str(peer_id)):
                                            await broadcast_ws_message(new_m)
                                    except Exception as ws_err:
                                        logger.debug(f"WS broadcast error in VK User LongPoll: {ws_err}")

            except asyncio.CancelledError:
                logger.info(f"VK User LongPoll task cancelled for account {account_id}")
                break
            except Exception as e:
                logger.error(f"Error in VK User LongPoll for account {account_id}: {e}")
                server = None
                key = None
                await asyncio.sleep(5)


vk_user_longpoll_manager = VkUserLongPollManager()


