import logging
import asyncio
import io
import os
import base64
import uuid
import time
import json
import httpx
from datetime import datetime, timezone
from typing import Optional, Dict, Any, List
from sqlmodel import Session, select
from app.core.database import engine
from app.models.chat import MultichatAccount, MultichatMessage

logger = logging.getLogger(__name__)

try:
    import qrcode
    HAS_QRCODE = True
except ImportError:
    HAS_QRCODE = False

try:
    import pymax
    from pymax.client_web import WebClient
    from pymax.auth.providers import QrHandler
    HAS_PYMAX = True
except ImportError:
    HAS_PYMAX = False
    logger.warning("pymax is not installed. Native MAX WebSocket bridge will use fallback.")

def _resolve_max_sessions_dir() -> str:
    """Определение постоянной директории хранения сессий MAX"""
    if os.path.exists("/app/media"):
        p = "/app/media/max_sessions"
        os.makedirs(p, exist_ok=True)
        return p
    candidates = [
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../admin/public/media/max_sessions")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../media/max_sessions")),
        os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../media/max_sessions")),
        "/media/max_sessions"
    ]
    for c in candidates:
        try:
            os.makedirs(c, exist_ok=True)
            return c
        except Exception:
            pass
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../media/max_sessions"))

# Каталог для хранения баз данных сессий MAX
MAX_SESSIONS_DIR = _resolve_max_sessions_dir()
os.makedirs(MAX_SESSIONS_DIR, exist_ok=True)

# Активные сессии спаривания по QR-коду MAX
active_max_bridge_sessions: Dict[str, Dict[str, Any]] = {}
active_max_web_clients: Dict[str, Any] = {}


class DynamicBridgeQrHandler(QrHandler if HAS_PYMAX else object):
    """Перехватчик реального QR-кода от серверов MAX"""
    def __init__(self, session_id: str):
        self.session_id = session_id
        self.qr_url: Optional[str] = None
        self.received_event = asyncio.Event()

    async def show_qr(self, qr_url: str) -> None:
        logger.info(f"Captured genuine MAX server QR for session {self.session_id}: {qr_url}")
        self.qr_url = qr_url
        self.received_event.set()


class MaxBridgeService:
    """
    Сессионный мост (Web Instance Bridge) для мессенджера MAX на базе PyMax.
    Поддерживает:
    - Получение подлинных QR-кодов авторизации https://max.ru/:auth/{track_id} напрямую от WebSocket серверов MAX
    - Менеджмент активных сессий (Keep-Alive, сохранение сессий в SQLite)
    - Синхронизацию диалогов и истории сообщений
    - Отправку сообщений клиентам от имени личного аккаунта
    """

    QR_EXPIRY_SECONDS = 90

    @staticmethod
    async def _close_pymax_client(client: Any) -> None:
        """Безопасное и полное закрытие PyMax WebClient и освобождение дескрипторов SQLite/сокетов"""
        if not client:
            return
        try:
            await client.close()
        except Exception:
            pass

        try:
            app = getattr(client, "_app", None)
            if app:
                store = getattr(app, "store", None)
                if store:
                    await store.close()
                conn = getattr(store, "conn", None)
                if conn:
                    await conn.close()
        except Exception:
            pass

    @staticmethod
    def _generate_qr_base64(data_str: str) -> str:
        """Генерация base64 PNG изображения QR-кода"""
        if not HAS_QRCODE or not data_str:
            return ""
        qr = qrcode.QRCode(
            version=None,
            error_correction=qrcode.constants.ERROR_CORRECT_M,
            box_size=8,
            border=2,
        )
        qr.add_data(data_str)
        qr.make(fit=True)
        img = qr.make_image(fill_color="black", back_color="white")
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode("utf-8")

    @classmethod
    async def init_qr_session(cls) -> Dict[str, Any]:
        """
        Инициализация реальной сессии привязки через WebSocket-рукопожатие с MAX.
        Запрашивает подлинный pairing URL (https://max.ru/:auth/{track_id}) у серверов MAX.
        """
        session_id = str(uuid.uuid4())
        session_db_name = f"max_session_{session_id[:8]}.db"
        
        qr_url = None
        client = None
        handler = None

        if HAS_PYMAX:
            try:
                handler = DynamicBridgeQrHandler(session_id)
                client = WebClient(
                    session_name=session_db_name,
                    work_dir=MAX_SESSIONS_DIR,
                    qr_provider=handler
                )

                # Регистрация обработчика успешного входа
                @client.on_start()
                async def _on_client_started(c: WebClient):
                    logger.info(f"PyMax WebClient successfully started/authorized for session {session_id}")
                    me = getattr(c._app, "me", None)
                    user_name = None
                    phone = None
                    if me:
                        phone = getattr(me, "phone", None)
                        names = getattr(me, "names", None)
                        if isinstance(names, dict):
                            user_name = f"{names.get('first_name', '')} {names.get('last_name', '')}".strip() or names.get("name")
                        elif isinstance(names, list) and len(names) > 0:
                            user_name = str(names[0])
                        if not user_name:
                            user_name = f"MAX Пользователь {getattr(me, 'id', '')}"

                    cls.confirm_bridge_session(
                        session_id=session_id,
                        phone=phone,
                        user_name=user_name or "Личный аккаунт MAX",
                        auth_token=session_db_name
                    )

                    # Запускаем синхронизацию диалогов
                    with Session(engine) as db:
                        await cls.sync_pymax_dialogs(db)

                # Регистрация слушателя входящих сообщений
                @client.on_message()
                async def _on_incoming_message(msg):
                    try:
                        await cls._handle_incoming_max_message(msg)
                    except Exception as me_err:
                        logger.error(f"Error handling incoming MAX message: {me_err}")

                # Запускаем фоновый таск клиента
                client_task = asyncio.create_task(client.start())
                active_max_web_clients[session_id] = {
                    "client": client,
                    "task": client_task,
                    "db_name": session_db_name
                }

                # Ожидаем появления QR-кода от сервера MAX
                try:
                    await asyncio.wait_for(handler.received_event.wait(), timeout=7.0)
                    qr_url = handler.qr_url
                except asyncio.TimeoutError:
                    logger.warning(f"Timeout waiting for MAX QR from WebSocket server for {session_id}")
            except Exception as e:
                logger.error(f"Failed to initialize live PyMax WebClient: {e}")

        # Fallback если библиотека или соединение с сервером не ответили вовремя
        if not qr_url:
            qr_url = f"https://max.ru/:auth/{session_id}"

        qr_base64 = cls._generate_qr_base64(qr_url)
        now = time.time()

        active_max_bridge_sessions[session_id] = {
            "session_id": session_id,
            "qr_payload": qr_url,
            "qr_base64": qr_base64,
            "created_at": now,
            "expires_at": now + cls.QR_EXPIRY_SECONDS,
            "status": "pending",
            "account_id": None,
            "phone": None,
            "user_name": None,
            "db_name": session_db_name
        }

        # Запускаем мониторинг авторизации
        asyncio.create_task(cls._watch_and_finalize_session(session_id))

        return {
            "session_id": session_id,
            "qr_payload": qr_url,
            "qr_base64": qr_base64,
            "expires_in": cls.QR_EXPIRY_SECONDS
        }

    @classmethod
    async def sync_pymax_dialogs(cls, db: Optional[Session] = None) -> int:
        """Синхронизация списка диалогов из подключенного аккаунта MAX в MultichatMessage"""
        if not HAS_PYMAX:
            return 0

        if db is None:
            with Session(engine) as s:
                accounts = s.exec(
                    select(MultichatAccount)
                    .where(MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"]))
                    .where(MultichatAccount.status == "active")
                ).all()
        else:
            accounts = db.exec(
                select(MultichatAccount)
                .where(MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"]))
                .where(MultichatAccount.status == "active")
            ).all()

        total_synced = 0
        for acc in accounts:
            meta = {}
            if acc.session_string:
                try:
                    meta = json.loads(acc.session_string)
                except Exception:
                    pass

            if meta.get("bridge_mode") != "pymax_web_instance":
                continue

            db_name = meta.get("db_name")
            if not db_name:
                continue

            db_path = os.path.join(MAX_SESSIONS_DIR, db_name)
            if not os.path.exists(db_path):
                logger.debug(f"Session DB file {db_path} not found for {acc.name}, skipping")
                continue

            client = None
            try:
                client = WebClient(session_name=db_name, work_dir=MAX_SESSIONS_DIR)
                try:
                    await asyncio.wait_for(client.connect(), timeout=10.0)
                except Exception as start_err:
                    logger.warning(f"Could not connect MAX client for {acc.name}: {start_err}")
                    continue

                if not getattr(client._app, "started", False):
                    continue

                try:
                    chats = await asyncio.wait_for(client.fetch_chats(), timeout=10.0)
                except Exception as fc_err:
                    logger.warning(f"Timeout/error fetching chats for {acc.name}: {fc_err}")
                    continue
                
                # Собираем ID пользователей для индивидуальных диалогов (chat_id > 0)
                user_ids = [ch.id for ch in chats if getattr(ch, "id", 0) > 0]
                user_map = {}
                if user_ids:
                    try:
                        users = await asyncio.wait_for(client.fetch_users(user_ids), timeout=8.0)
                        user_map = {u.id: u for u in users}
                        logger.info(f"Resolved {len(user_map)} MAX user profiles for chat enrichment")
                    except Exception as ue:
                        logger.warning(f"Failed to fetch MAX users: {ue}")

                def _save_chats_to_db(target_db):
                    nonlocal total_synced
                    for ch in chats:
                        chat_id = getattr(ch, "id", None)
                        if not chat_id:
                            continue
                        peer_id = str(chat_id)
                        
                        title = getattr(ch, "title", None)
                        avatar = getattr(ch, "base_url", None) or getattr(ch, "base_raw_url", None)
                        phone = None
                        
                        # Если это личный диалог с пользователем
                        if chat_id in user_map:
                            u = user_map[chat_id]
                            phone = getattr(u, "phone", None)
                            avatar = getattr(u, "base_url", None) or getattr(u, "base_raw_url", None) or avatar
                            names = getattr(u, "names", None)
                            if names:
                                if isinstance(names, list) and len(names) > 0:
                                    first_item = names[0]
                                    if hasattr(first_item, "first_name") or hasattr(first_item, "last_name"):
                                        f = getattr(first_item, "first_name", "") or ""
                                        l = getattr(first_item, "last_name", "") or ""
                                        n = getattr(first_item, "name", "") or ""
                                        full = f"{f} {l}".strip()
                                        title = full or n or title
                                    elif isinstance(first_item, str):
                                        title = first_item
                                elif isinstance(names, dict):
                                    f = names.get("first_name", "")
                                    l = names.get("last_name", "")
                                    full = f"{f} {l}".strip()
                                    title = full or names.get("name") or title
                            if not title:
                                username = getattr(u, "username", None) or getattr(u, "link", None)
                                title = f"@{username}" if username else f"Пользователь MAX {peer_id}"
                        elif not title:
                            title = f"Чат {peer_id}"

                        # Пропускаем пустые чаты без единого сообщения, чтобы не засорять базу фейками "Диалог MAX"
                        last_msg = getattr(ch, "last_message", None)
                        if not last_msg:
                            continue

                        text = getattr(last_msg, "text", "") or ""
                        attaches = getattr(last_msg, "attaches", None)
                        if not text and attaches:
                            att_types = []
                            for a in (attaches if isinstance(attaches, list) else [attaches]):
                                a_type = getattr(a, "type", None) or (a.get("type") if isinstance(a, dict) else "Вложение")
                                att_types.append(str(a_type).capitalize())
                            text = f"[{', '.join(att_types) if att_types else 'Вложение'}]"
                        elif not text:
                            text = "[Сообщение]"

                        msg_time = getattr(last_msg, "time", None) or time.time()
                        if msg_time > 1e11:
                            msg_time = msg_time / 1000
                        msg_date = datetime.fromtimestamp(msg_time, tz=timezone.utc)
                        
                        m_id = getattr(last_msg, "id", None)
                        ext_id = f"max_msg_{m_id}" if m_id else f"max_{peer_id}_{int(msg_time)}"

                        # Проверяем направление (исходящее или входящее)
                        sender_obj = getattr(last_msg, "sender", None)
                        sender_id_val = str(getattr(sender_obj, "id", "") if sender_obj else peer_id)
                        my_id_val = str(getattr(client._app.me, "id", "")) if hasattr(client, "_app") and getattr(client._app, "me", None) else ""
                        is_outbound = bool(my_id_val and sender_id_val == my_id_val)
                        direction = "outbound" if is_outbound else "inbound"

                        # Обогащаем имя клиента через CRM Customer
                        if not title or "пользователь" in title.lower() or title.startswith("Чат "):
                            from app.models.customer import Customer
                            cust = target_db.exec(select(Customer).where((Customer.max_user_id == peer_id) | (Customer.phone == phone) | (Customer.phone == peer_id))).first()
                            if cust:
                                c_name = f"{cust.first_name or cust.name or ''} {cust.last_name or cust.surname or ''}".strip()
                                if c_name:
                                    title = c_name
                                if not phone and cust.phone:
                                    phone = cust.phone
                        
                        payload = {
                            "phone": phone,
                            "avatar_url": avatar,
                            "user_id": chat_id,
                            "raw_message_id": m_id
                        }
                        
                        # Проверяем наличие конкретного сообщения по external_id
                        existing_by_ext = target_db.exec(
                            select(MultichatMessage)
                            .where(MultichatMessage.channel == "max_user")
                            .where(MultichatMessage.external_id == ext_id)
                        ).first()
                        
                        existing_dialog = target_db.exec(
                            select(MultichatMessage)
                            .where(MultichatMessage.channel == "max_user")
                            .where(MultichatMessage.peer_id == peer_id)
                        ).first()
                        
                        if not existing_by_ext:
                            is_new_message = (existing_dialog is not None and existing_dialog.text != text)
                            new_msg = MultichatMessage(
                                channel="max_user",
                                channel_id=str(acc.id),
                                peer_id=peer_id,
                                peer_name=title,
                                peer_avatar=avatar,
                                from_id=sender_id_val,
                                text=text,
                                direction=direction,
                                external_id=ext_id,
                                created_at=msg_date,
                                is_read=True if is_outbound else (not is_new_message),
                                payload=payload
                            )
                            target_db.add(new_msg)
                            total_synced += 1
                            
                            # Транслируем новое входящее сообщение операторам через WebSocket
                            if not is_outbound and is_new_message:
                                try:
                                    from app.api.multichat import broadcast_ws_message
                                    asyncio.create_task(broadcast_ws_message(new_msg))
                                except Exception:
                                    pass
                                try:
                                    from app.api.notifications import log_system_notification
                                    log_system_notification(
                                        db=target_db,
                                        title=f"Сообщение MAX от {title}",
                                        subtitle="Мессенджер MAX (Личный номер)",
                                        body=text or "[Медиа/Вложение]",
                                        event_type="max_message",
                                        category="max_message",
                                        url="/multichat",
                                        badge_text="MAX (Личный №)",
                                        badge_color="success",
                                        external_key=f"max_msg_{ext_msg_id}"
                                    )
                                except Exception as max_feed_err:
                                    logger.warning(f"Error logging MAX feed notification: {max_feed_err}")
                        
                        if existing_dialog:
                            existing_dialog.peer_name = title
                            existing_dialog.peer_avatar = avatar
                            existing_dialog.text = text
                            existing_dialog.created_at = msg_date
                            existing_dialog.payload = payload
                            target_db.add(existing_dialog)

                    target_db.commit()

                if db is not None:
                    _save_chats_to_db(db)
                else:
                    with Session(engine) as target_db:
                        _save_chats_to_db(target_db)
            except Exception as e:
                logger.warning(f"Error in sync_pymax_dialogs for {acc.name}: {e}")
            finally:
                if client:
                    await cls._close_pymax_client(client)

        return total_synced


    @classmethod
    async def fetch_chat_history(cls, peer_id: str, db: Session, count: int = 40) -> int:
        """Загрузка истории сообщений конкретного диалога из MAX"""
        acc = db.exec(
            select(MultichatAccount)
            .where(MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"]))
            .where(MultichatAccount.status == "active")
        ).first()
        if not acc:
            return 0

        meta = {}
        if acc.session_string:
            try:
                meta = json.loads(acc.session_string)
            except Exception:
                pass

        if meta.get("bridge_mode") != "pymax_web_instance":
            return 0

        db_name = meta.get("db_name")
        if not HAS_PYMAX or not db_name:
            return 0

        db_path = os.path.join(MAX_SESSIONS_DIR, db_name)
        if not os.path.exists(db_path):
            return 0

        try:
            int_chat_id = int(peer_id)
        except ValueError:
            return 0

        client = None
        try:
            client = WebClient(session_name=db_name, work_dir=MAX_SESSIONS_DIR)
            try:
                await asyncio.wait_for(client.connect(), timeout=10.0)
            except Exception as start_err:
                logger.warning(f"Could not connect MAX client for history {peer_id}: {start_err}")
                return 0

            if not getattr(client._app, "started", False):
                return 0

            messages = await asyncio.wait_for(client.fetch_history(chat_id=int_chat_id, backward=count), timeout=10.0)
            saved = 0
            my_id = str(getattr(client._app.me, "id", ""))

            # Определяем реальное имя собеседника и аватар
            real_name = None
            real_avatar = None
            existing_dialog = db.exec(
                select(MultichatMessage)
                .where(MultichatMessage.channel == "max_user", MultichatMessage.peer_id == peer_id)
                .where(~MultichatMessage.peer_name.ilike("%пользователь%"), ~MultichatMessage.peer_name.startswith("MAX "))
            ).first()
            if existing_dialog:
                real_name = existing_dialog.peer_name
                real_avatar = existing_dialog.peer_avatar

            for m in messages:
                m_id = getattr(m, "id", None)
                if not m_id:
                    continue
                ext_id = f"max_msg_{m_id}"
                
                existing = db.exec(
                    select(MultichatMessage)
                    .where(MultichatMessage.external_id == ext_id)
                ).first()
                
                if not existing:
                    text = getattr(m, "text", "") or "[Медиа / Вложение]"
                    sender = getattr(m, "sender", None)
                    from_id = str(getattr(sender, "id", peer_id) if sender else peer_id)
                    m_time = getattr(m, "time", None) or time.time()
                    if m_time > 1e11:
                        m_time = m_time / 1000
                    m_date = datetime.fromtimestamp(m_time, tz=timezone.utc)
                    
                    is_out = (from_id == my_id)
                    
                    new_msg = MultichatMessage(
                        channel="max_user",
                        channel_id=str(acc.id),
                        peer_id=peer_id,
                        peer_name=real_name or f"MAX {peer_id}",
                        peer_avatar=real_avatar,
                        from_id=from_id,
                        text=text,
                        direction="outbound" if is_out else "inbound",
                        external_id=ext_id,
                        created_at=m_date,
                        is_read=True
                    )
                    db.add(new_msg)
                    saved += 1
            db.commit()
            return saved
        except Exception as e:
            logger.warning(f"Error fetching MAX chat history for {peer_id}: {e}")
            return 0
        finally:
            if client:
                await cls._close_pymax_client(client)

    @classmethod
    async def _handle_incoming_max_message(cls, msg):
        """Сохранение входящего сообщения от пользователя MAX в базу Мультичата"""
        chat_id = getattr(msg, "chat_id", None)
        text = getattr(msg, "text", "") or "[Вложение / Медиа]"
        sender = getattr(msg, "sender", None)
        user_name = "Пользователь MAX"
        avatar_url = None
        if sender:
            avatar_url = getattr(sender, "base_url", None) or getattr(sender, "base_raw_url", None)
            names = getattr(sender, "names", None)
            if isinstance(names, dict):
                user_name = f"{names.get('first_name', '')} {names.get('last_name', '')}".strip() or names.get("name")
            elif isinstance(names, list) and len(names) > 0:
                first_item = names[0]
                if hasattr(first_item, "first_name") or hasattr(first_item, "last_name"):
                    f = getattr(first_item, "first_name", "") or ""
                    l = getattr(first_item, "last_name", "") or ""
                    user_name = f"{f} {l}".strip() or getattr(first_item, "name", "")
                elif isinstance(first_item, str):
                    user_name = first_item

        peer_id = str(chat_id or (sender.id if sender else "unknown"))
        
        with Session(engine) as db:
            from app.models.customer import Customer
            from app.models.chat import MultichatAccount
            
            acc = db.exec(
                select(MultichatAccount)
                .where(MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"]))
                .where(MultichatAccount.status == "active")
            ).first()
            acc_id_str = str(acc.id) if acc else None

            cust = db.exec(select(Customer).where((Customer.max_user_id == peer_id) | (Customer.phone == peer_id))).first()
            if cust:
                c_name = f"{cust.first_name or cust.name or ''} {cust.last_name or cust.surname or ''}".strip()
                if c_name:
                    user_name = c_name
            elif user_name == "Пользователь MAX" or user_name.startswith("MAX "):
                existing_msg = db.exec(
                    select(MultichatMessage)
                    .where(MultichatMessage.channel == "max_user", MultichatMessage.peer_id == peer_id)
                    .where(~MultichatMessage.peer_name.ilike("%пользователь%"), ~MultichatMessage.peer_name.startswith("MAX "))
                ).first()
                if existing_msg and existing_msg.peer_name:
                    user_name = existing_msg.peer_name
                    avatar_url = avatar_url or existing_msg.peer_avatar

            chat_msg = MultichatMessage(
                channel="max_user",
                channel_id=acc_id_str,
                peer_id=peer_id,
                peer_name=user_name,
                peer_avatar=avatar_url,
                from_id=str(sender.id if sender else peer_id),
                direction="inbound",
                text=text,
                created_at=datetime.now(timezone.utc),
                is_read=False
            )
            db.add(chat_msg)
            db.commit()
            db.refresh(chat_msg)
            logger.info(f"Incoming MAX message saved from {user_name} ({peer_id}): {text[:30]}")

            # Обработка входящего сообщения маркетинговыми ботами (NPS оценка, команды меню магазина)
            try:
                from app.services.vk_marketing_bots_service import VkMarketingBotsService
                asyncio.create_task(VkMarketingBotsService.handle_max_incoming_message(db, peer_id, text, user_name))
            except Exception as bot_err:
                logger.debug(f"Error dispatching MAX message to marketing bots: {bot_err}")

            try:
                from app.api.multichat import broadcast_ws_message
                asyncio.create_task(broadcast_ws_message(chat_msg))
            except Exception as e:
                logger.debug(f"WS broadcast error for MAX message: {e}")

    @classmethod
    async def _watch_and_finalize_session(cls, session_id: str):
        """Ожидание сканирования QR-кода пользователем и регистрация аккаунта"""
        client_info = active_max_web_clients.get(session_id)
        
        while session_id in active_max_bridge_sessions:
            sess = active_max_bridge_sessions[session_id]
            if sess["status"] == "active":
                break
            if time.time() > sess["expires_at"]:
                sess["status"] = "expired"
                if client_info and client_info.get("client"):
                    try:
                        await client_info["client"].stop()
                    except Exception:
                        pass
                logger.info(f"MAX Bridge pairing session {session_id} expired")
                break

            # Если клиент успешно авторизовался через WebSocket
            if client_info and client_info.get("client"):
                client = client_info["client"]
                try:
                    if getattr(client._app, "started", False):
                        me = getattr(client._app, "me", None)
                        user_name = None
                        phone = None
                        if me:
                            phone = getattr(me, "phone", None)
                            names = getattr(me, "names", None)
                            if isinstance(names, dict):
                                user_name = f"{names.get('first_name', '')} {names.get('last_name', '')}".strip() or names.get("name")
                            elif isinstance(names, list) and len(names) > 0:
                                user_name = str(names[0])
                            if not user_name:
                                user_name = f"MAX Пользователь {getattr(me, 'id', '')}"
                        
                        cls.confirm_bridge_session(
                            session_id=session_id,
                            phone=phone,
                            user_name=user_name or "Личный аккаунт MAX",
                            auth_token=client_info["db_name"]
                        )
                        break
                except Exception as e:
                    logger.debug(f"Watch check note: {e}")

            await asyncio.sleep(1.5)

    @classmethod
    def get_session_status(cls, session_id: str) -> Dict[str, Any]:
        """Получение статуса сессии спаривания"""
        sess = active_max_bridge_sessions.get(session_id)
        if not sess:
            return {"status": "expired", "message": "Сессия не найдена"}
        
        # Проверяем, не авторизовался ли PyMax клиент
        client_info = active_max_web_clients.get(session_id)
        if client_info and client_info.get("client"):
            client = client_info["client"]
            if getattr(client._app, "started", False) and sess["status"] != "active":
                me = getattr(client._app, "me", None)
                user_name = None
                phone = None
                if me:
                    phone = getattr(me, "phone", None)
                    names = getattr(me, "names", None)
                    if isinstance(names, dict):
                        user_name = f"{names.get('first_name', '')} {names.get('last_name', '')}".strip() or names.get("name")
                    elif isinstance(names, list) and len(names) > 0:
                        user_name = str(names[0])
                    if not user_name:
                        user_name = f"MAX Пользователь {getattr(me, 'id', '')}"

                cls.confirm_bridge_session(
                    session_id=session_id,
                    phone=phone,
                    user_name=user_name or "Личный аккаунт MAX",
                    auth_token=client_info["db_name"]
                )

        time_left = max(0, int(sess["expires_at"] - time.time()))
        if time_left == 0 and sess["status"] == "pending":
            sess["status"] = "expired"

        return {
            "session_id": session_id,
            "status": sess["status"],
            "time_left": time_left,
            "phone": sess.get("phone"),
            "user_name": sess.get("user_name"),
            "account_id": sess.get("account_id")
        }

    @classmethod
    def confirm_bridge_session(
        cls, 
        session_id: str, 
        phone: Optional[str] = None, 
        user_name: Optional[str] = None,
        auth_token: Optional[str] = None
    ) -> MultichatAccount:
        """
        Подтверждение подключения инстанса MAX.
        Создает или обновляет запись в MultichatAccount.
        """
        sess = active_max_bridge_sessions.get(session_id)
        
        clean_phone = "".join(filter(str.isdigit, phone or "")) if phone else None
        if clean_phone and not clean_phone.startswith("7") and len(clean_phone) == 10:
            clean_phone = "7" + clean_phone
        elif clean_phone and clean_phone.startswith("8") and len(clean_phone) == 11:
            clean_phone = "7" + clean_phone[1:]

        formatted_phone = f"+{clean_phone}" if clean_phone else None
        name = user_name or (f"MAX {formatted_phone}" if formatted_phone else "Личный аккаунт MAX")
        token = auth_token or f"max_bridge_{uuid.uuid4().hex}"
        db_name = sess.get("db_name") if sess else f"max_session_{session_id[:8]}.db"

        with Session(engine) as db:
            query = select(MultichatAccount).where(
                MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"])
            )
            if formatted_phone:
                query = query.where(MultichatAccount.phone == formatted_phone)
            else:
                query = query.where(MultichatAccount.name == name)

            account = db.exec(query).first()
            session_meta = {
                "bridge_session_id": session_id,
                "db_name": db_name,
                "paired_at": datetime.now(timezone.utc).isoformat(),
                "bridge_mode": "pymax_web_instance"
            }

            if account:
                account.token = token
                account.session_string = json.dumps(session_meta)
                account.status = "active"
                if formatted_phone:
                    account.phone = formatted_phone
                account.name = name
                db.add(account)
            else:
                account = MultichatAccount(
                    channel="max_user",
                    name=name,
                    phone=formatted_phone,
                    token=token,
                    session_string=json.dumps(session_meta),
                    status="active"
                )
                db.add(account)

            db.commit()
            db.refresh(account)

        if sess:
            sess["status"] = "active"
            sess["phone"] = formatted_phone
            sess["user_name"] = name
            sess["account_id"] = account.id

        logger.info(f"MAX Bridge account successfully activated: {name} (ID: {account.id})")
        return account

    @classmethod
    def disconnect_session(cls, account_id: int) -> bool:
        """Отключение сессии моста MAX"""
        with Session(engine) as db:
            acc = db.get(MultichatAccount, account_id)
            if acc and acc.channel in ["max_user", "max_bridge", "max_account"]:
                acc.status = "disconnected"
                acc.session_string = None
                db.add(acc)
                db.commit()
                return True
        return False

    @classmethod
    async def send_bridge_message(cls, peer_id: str, text: str, db: Session, image_path: Optional[str] = None, image_url: Optional[str] = None) -> Dict[str, Any]:
        """
        Отправка сообщения через сессию MAX Bridge.
        """
        acc = db.exec(
            select(MultichatAccount)
            .where(MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"]))
            .where(MultichatAccount.status == "active")
        ).first()

        if not acc:
            raise ValueError("Нет активного подключенного аккаунта MAX (Web Bridge)")

        session_meta = {}
        if acc.session_string:
            try:
                session_meta = json.loads(acc.session_string)
            except Exception:
                pass

        db_name = session_meta.get("db_name") or acc.token
        resolved_peer_id = peer_id
        last_error = None
        if HAS_PYMAX and db_name:
            client = None
            try:
                client = WebClient(session_name=db_name, work_dir=MAX_SESSIONS_DIR)
                await asyncio.wait_for(client.connect(), timeout=12.0)

                # Определение своего ID (отправителя)
                my_user_id = None
                if hasattr(client, "me") and client.me:
                    my_user_id = getattr(client.me.contact, "id", None) if hasattr(client.me, "contact") else getattr(client.me, "id", None)
                if not my_user_id and hasattr(client, "_app") and getattr(client._app, "me", None):
                    me_obj = client._app.me
                    my_user_id = getattr(me_obj.contact, "id", None) if hasattr(me_obj, "contact") else getattr(me_obj, "id", None)

                target_user_id: Optional[int] = None

                # Проверяем, является ли peer_id номером телефона
                clean_p = "".join(filter(str.isdigit, str(peer_id)))
                if len(clean_p) in (10, 11) and not str(peer_id).startswith("-"):
                    if len(clean_p) == 11 and clean_p.startswith("8"):
                        phone_search = "7" + clean_p[1:]
                    elif len(clean_p) == 10:
                        phone_search = "7" + clean_p
                    else:
                        phone_search = clean_p
                    try:
                        found_u = await asyncio.wait_for(client.search_by_phone(phone_search), timeout=8.0)
                        if found_u and getattr(found_u, "id", None):
                            target_user_id = int(found_u.id)
                            resolved_peer_id = str(found_u.id)
                            logger.info(f"PyMax resolved phone {phone_search} to user ID {resolved_peer_id}")

                            # Автоматически сохраняем max_user_id в карточку клиента Customer
                            try:
                                from app.models.customer import Customer
                                cust = db.exec(select(Customer).where(Customer.phone.like(f"%{phone_search[-10:]}%"))).first()
                                if cust and not cust.max_user_id:
                                    cust.max_user_id = str(found_u.id)
                                    db.add(cust)
                                    db.commit()
                                    logger.info(f"Auto-linked Customer #{cust.id} to MAX ID {found_u.id}")
                            except Exception as link_err:
                                logger.warning(f"Error auto-linking customer during send: {link_err}")
                        else:
                            raise ValueError(f"Пользователь с номером {phone_search} не зарегистрирован в MAX")
                    except Exception as search_err:
                        logger.warning(f"PyMax search_by_phone for {phone_search} failed during send: {search_err}")
                        raise search_err
                elif str(resolved_peer_id).isdigit():
                    target_user_id = int(resolved_peer_id)

                # Вычисляем chat_id:
                # В протоколе MAX ID диалога тет-а-тет вычисляется через get_chat_id(my_user_id, target_user_id)
                if my_user_id and target_user_id:
                    int_chat_id = client.get_chat_id(my_user_id, target_user_id)
                    logger.info(f"Calculated MAX 1-to-1 chat_id={int_chat_id} (my_id={my_user_id}, target_id={target_user_id})")
                elif str(resolved_peer_id).startswith("-"):
                    # Групповой чат
                    int_chat_id = int(resolved_peer_id)
                else:
                    int_chat_id = int(resolved_peer_id) if str(resolved_peer_id).isdigit() else resolved_peer_id

                attachments = []
                if image_path:
                    try:
                        from pymax.files.photo import Photo
                        attachments.append(Photo(path=image_path))
                    except Exception as att_err:
                        logger.warning(f"Failed to create Photo from path {image_path}: {att_err}")
                elif image_url:
                    try:
                        from pymax.files.photo import Photo
                        attachments.append(Photo(url=image_url))
                    except Exception as att_err:
                        logger.warning(f"Failed to create Photo from url {image_url}: {att_err}")

                res = await asyncio.wait_for(client.send_message(chat_id=int_chat_id, text=text, attachments=attachments or None), timeout=12.0)
                msg_id = getattr(res, "id", None) or f"max_{int(time.time())}"
                return {"status": "success", "msg_id": str(msg_id)}
            except Exception as pe:
                last_error = pe
                logger.warning(f"PyMax direct send note: {pe}, attempting REST fallback")
            finally:
                if client:
                    await cls._close_pymax_client(client)

        # REST fallback через platform-api2 (только если указан токен бота)
        if acc.token and acc.token.strip():
            headers = {
                "Authorization": acc.token,
                "Content-Type": "application/json"
            }
            payload = {
                "chat_id": resolved_peer_id,
                "text": text
            }

            try:
                async with httpx.AsyncClient(verify=False, timeout=10.0) as http_client:
                    resp = await http_client.post(
                        f"https://platform-api2.max.ru/messages?chat_id={peer_id}", 
                        headers=headers, 
                        json=payload
                    )
                    if resp.status_code in [200, 201]:
                        res_json = resp.json()
                        mid = res_json.get("message", {}).get("id") or res_json.get("id") or f"rest_{int(time.time())}"
                        return {"status": "success", "msg_id": str(mid)}
                    else:
                        last_error = f"HTTP {resp.status_code}: {resp.text}"
            except Exception as e:
                logger.warning(f"MAX bridge HTTP fallback warning: {e}")
                last_error = e

        # Если отправка не удалась — возбуждаем исключение
        err_text = str(last_error) if last_error else "Не удалось отправить сообщение через аккаунт MAX"
        logger.error(f"send_bridge_message failed for {peer_id}: {err_text}")
        raise RuntimeError(err_text)

    @classmethod
    async def search_user_by_phone(cls, phone: str, db: Session) -> dict:
        """Поиск пользователя MAX по номеру телефона в реальном времени"""
        clean_phone = "".join(filter(str.isdigit, str(phone)))
        if len(clean_phone) == 11 and clean_phone.startswith("8"):
            clean_phone = "7" + clean_phone[1:]
        elif len(clean_phone) == 10:
            clean_phone = "7" + clean_phone

        acc = db.exec(
            select(MultichatAccount)
            .where(MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"]))
            .where(MultichatAccount.status == "active")
        ).first()

        if not acc or not HAS_PYMAX:
            return {"found": False, "error": "Активный аккаунт MAX не подключен"}

        meta = {}
        if acc.session_string:
            try:
                meta = json.loads(acc.session_string)
            except Exception:
                pass

        db_name = meta.get("db_name")
        if not db_name:
            return {"found": False, "error": "Файл сессии MAX не найден"}

        db_path = os.path.join(MAX_SESSIONS_DIR, db_name)
        if not os.path.exists(db_path):
            return {"found": False, "error": f"Файл сессии {db_name} не найден"}

        client = None
        try:
            client = WebClient(session_name=db_name, work_dir=MAX_SESSIONS_DIR)
            try:
                await asyncio.wait_for(client.connect(), timeout=10.0)
            except Exception as start_err:
                return {"found": False, "error": f"Не удалось подключиться к сессии MAX: {start_err}"}

            max_u = await asyncio.wait_for(client.search_by_phone(clean_phone), timeout=10.0)

            if not max_u or not getattr(max_u, "id", None):
                return {"found": False, "error": "Пользователь с таким номером телефона не зарегистрирован в MAX"}

            user_id = str(max_u.id)
            names = getattr(max_u, "names", None)
            full_name = ""
            if names and isinstance(names, list) and len(names) > 0:
                first_item = names[0]
                f = getattr(first_item, "first_name", "") or ""
                l = getattr(first_item, "last_name", "") or ""
                n = getattr(first_item, "name", "") or ""
                full_name = f"{f} {l}".strip() or n
            
            avatar = getattr(max_u, "base_url", None) or getattr(max_u, "base_raw_url", None)
            
            # Сопоставляем с базой клиентов
            from app.models.customer import Customer
            customer = db.exec(select(Customer).where(Customer.phone.like(f"%{clean_phone[-10:]}%"))).first()
            customer_data = None
            if customer:
                customer.max_user_id = user_id
                db.add(customer)
                db.commit()
                customer_data = {
                    "id": customer.id,
                    "name": customer.name or full_name,
                    "phone": customer.phone,
                    "bonus_points": float(customer.bonus_points or 0),
                    "total_orders_count": customer.total_orders_count or 0
                }

            formatted_phone = f"+7 ({clean_phone[1:4]}) {clean_phone[4:7]}-{clean_phone[7:9]}-{clean_phone[9:11]}"

            return {
                "found": True,
                "user_id": user_id,
                "name": full_name or (customer.name if customer else f"Пользователь MAX {user_id}"),
                "phone": formatted_phone,
                "raw_phone": clean_phone,
                "avatar_url": avatar,
                "customer": customer_data
            }

        except Exception as e:
            logger.warning(f"Error in search_user_by_phone for {phone}: {e}")
            err_msg = str(e)
            if "not.found" in err_msg.lower() or "not found" in err_msg.lower():
                return {"found": False, "error": "Пользователь с таким номером телефона не зарегистрирован в MAX"}
            return {"found": False, "error": f"Ошибка поиска: {err_msg}"}
        finally:
            if client:
                await cls._close_pymax_client(client)

    @classmethod
    async def link_customer_by_phone(cls, phone: str, customer_id: Optional[int] = None, db: Optional[Session] = None) -> Optional[str]:
        """
        Поиск пользователя в MAX по номеру телефона и привязка max_user_id к карточке гостя.
        Возвращает max_user_id если найден, либо None.
        """
        if not phone:
            return None

        clean_p = "".join(filter(str.isdigit, str(phone)))
        if len(clean_p) == 11 and clean_p.startswith("8"):
            clean_phone = "7" + clean_p[1:]
        elif len(clean_p) == 10:
            clean_phone = "7" + clean_p
        else:
            clean_phone = clean_p

        if len(clean_phone) != 11:
            return None

        own_session = False
        if db is None:
            db = Session(engine)
            own_session = True

        try:
            from app.models.customer import Customer

            customer = None
            if customer_id:
                customer = db.get(Customer, customer_id)
            if not customer:
                customer = db.exec(select(Customer).where(Customer.phone.like(f"%{clean_phone[-10:]}%"))).first()

            if customer and customer.max_user_id:
                return str(customer.max_user_id)

            search_res = await cls.search_user_by_phone(clean_phone, db)
            if search_res.get("found") and search_res.get("user_id"):
                max_uid = str(search_res["user_id"])
                if customer:
                    customer.max_user_id = max_uid
                    db.add(customer)
                    db.commit()
                    db.refresh(customer)
                    logger.info(f"Successfully linked Customer #{customer.id} ({customer.phone}) with MAX ID {max_uid}")
                return max_uid
            return None
        except Exception as e:
            logger.warning(f"Failed to link customer by phone {phone} to MAX: {e}")
            return None
        finally:
            if own_session:
                db.close()

    @classmethod
    async def batch_search_customers(cls, db: Session, limit: int = 50) -> Dict[str, Any]:
        """Пакетный поиск пользователей MAX для клиентов без max_user_id"""
        from app.models.customer import Customer
        customers = db.exec(
            select(Customer)
            .where(Customer.phone.is_not(None))
            .where(Customer.max_user_id.is_(None))
            .limit(limit)
        ).all()
        
        if not customers:
            return {"total": 0, "found_count": 0, "details": []}
            
        acc = db.exec(
            select(MultichatAccount)
            .where(MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"]))
            .where(MultichatAccount.status == "active")
        ).first()

        if not acc or not HAS_PYMAX:
            return {"total": len(customers), "found_count": 0, "error": "Активный аккаунт MAX не подключен"}

        meta = {}
        if acc.session_string:
            try:
                meta = json.loads(acc.session_string)
            except Exception:
                pass

        db_name = meta.get("db_name")
        if not db_name or not os.path.exists(os.path.join(MAX_SESSIONS_DIR, db_name)):
            return {"total": len(customers), "found_count": 0, "error": "Файл сессии MAX не найден"}

        client = None
        found_count = 0
        details = []
        try:
            client = WebClient(session_name=db_name, work_dir=MAX_SESSIONS_DIR)
            await asyncio.wait_for(client.connect(), timeout=10.0)
            
            for c in customers:
                clean_phone = "".join(filter(str.isdigit, str(c.phone or "")))
                if len(clean_phone) == 11 and clean_phone.startswith("8"):
                    clean_phone = "7" + clean_phone[1:]
                elif len(clean_phone) == 10:
                    clean_phone = "7" + clean_phone

                if len(clean_phone) != 11:
                    continue

                try:
                    max_u = await asyncio.wait_for(client.search_by_phone(clean_phone), timeout=6.0)
                    if max_u and getattr(max_u, "id", None):
                        c.max_user_id = str(max_u.id)
                        db.add(c)
                        found_count += 1
                        details.append({
                            "customer_id": c.id,
                            "phone": c.phone,
                            "max_user_id": str(max_u.id),
                            "status": "matched"
                        })
                    else:
                        details.append({
                            "customer_id": c.id,
                            "phone": c.phone,
                            "status": "not_registered"
                        })
                except Exception as ex:
                    details.append({
                        "customer_id": c.id,
                        "phone": c.phone,
                        "status": "error",
                        "error": str(ex)
                    })
                await asyncio.sleep(0.3)
                
            db.commit()
        except Exception as e:
            logger.error(f"Error in batch_search_customers: {e}")
            return {"total": len(customers), "found_count": found_count, "error": str(e), "details": details}
        finally:
            if client:
                await cls._close_pymax_client(client)

        return {"total": len(customers), "found_count": found_count, "details": details}

    @classmethod
    async def start_persistent_bridge_clients(cls):
        """
        Автоматический запуск фоновых постоянных слушателей PyMax WebClient
        для всех активных личных аккаунтов MAX при старте бэкенда.
        Обеспечивает прием сообщений в реальном времени через WebSocket без задержек.
        """
        if not HAS_PYMAX:
            logger.warning("PyMax не установлен, фоновый слушатель MAX WebClient не может быть запущен")
            return

        logger.info("Запуск фоновых слушателей MAX WebClient...")
        try:
            with Session(engine) as db:
                accounts = db.exec(
                    select(MultichatAccount)
                    .where(MultichatAccount.channel.in_(["max_user", "max_bridge", "max_account"]))
                    .where(MultichatAccount.status == "active")
                ).all()

                for acc in accounts:
                    meta = {}
                    if acc.session_string:
                        try:
                            meta = json.loads(acc.session_string)
                        except Exception:
                            pass

                    db_name = meta.get("db_name")
                    if not db_name:
                        continue

                    db_path = os.path.join(MAX_SESSIONS_DIR, db_name)
                    if not os.path.exists(db_path):
                        logger.warning(f"Файл сессии MAX {db_path} для {acc.name} не найден, пропуск")
                        continue

                    bridge_session_id = meta.get("bridge_session_id") or str(acc.id)
                    existing = active_max_web_clients.get(bridge_session_id)
                    if existing and existing.get("task") and not existing["task"].done():
                        logger.info(f"Слушатель MAX для аккаунта {acc.name} уже активен")
                        continue

                    try:
                        logger.info(f"Инициализация постоянного WebClient MAX для {acc.name} ({db_name})")
                        client = WebClient(
                            session_name=db_name,
                            work_dir=MAX_SESSIONS_DIR
                        )

                        @client.on_message()
                        async def _on_incoming(msg):
                            try:
                                await cls._handle_incoming_max_message(msg)
                            except Exception as ex:
                                logger.error(f"Ошибка в слушателе входящих сообщений MAX: {ex}")

                        client_task = asyncio.create_task(client.start())
                        active_max_web_clients[bridge_session_id] = {
                            "client": client,
                            "task": client_task,
                            "db_name": db_name,
                            "account_id": acc.id
                        }
                        logger.info(f"Фоновый слушатель MAX успешно запущен для {acc.name}")
                    except Exception as client_err:
                        logger.error(f"Не удалось инициализировать WebClient MAX для {acc.name}: {client_err}")

            # После запуска слушателей синхронизируем накопившиеся диалоги
            await asyncio.sleep(2)
            synced = await cls.sync_pymax_dialogs()
            logger.info(f"Первичная синхронизация MAX завершена, синхронизировано {synced} диалогов")
        except Exception as e:
            logger.error(f"Ошибка в start_persistent_bridge_clients: {e}")


max_bridge_service = MaxBridgeService()

