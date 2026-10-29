from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect, HTTPException, status, Query
from sqlmodel import Session, select, desc, func, and_, or_
from sqlalchemy.orm import joinedload
from app.api import deps
from app.models.user import User
from app.models.chat import ChatMessage, ChatReadState
from app.schemas.chat import (
    ChatMessageRead, ChatMessageCreate, ChatContact, 
    ChatHistoryResponse, ChatReadRequest
)
from datetime import datetime, timezone
import json
import asyncio
import os
import uuid
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])

PROCESS_INSTANCE_ID = f"{os.getpid()}_{uuid.uuid4().hex[:8]}"
REDIS_WS_CHANNEL = "foodtech:ws_broadcast"

class ConnectionManager:
    def __init__(self):
        # user_id -> list of websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}
        self.loop: Optional[asyncio.AbstractEventLoop] = None
        self._listener_started: bool = False

    async def connect(self, user_id: int, websocket: WebSocket):
        try:
            self.loop = asyncio.get_running_loop()
        except RuntimeError:
            pass
        await websocket.accept()
        if user_id not in self.active_connections:
            self.active_connections[user_id] = []
        self.active_connections[user_id].append(websocket)

    def disconnect(self, user_id: int, websocket: WebSocket):
        if user_id in self.active_connections:
            if websocket in self.active_connections[user_id]:
                self.active_connections[user_id].remove(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]

    async def send_personal_message(self, message: dict, user_id: int):
        if user_id in self.active_connections:
            for connection in list(self.active_connections[user_id]):
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def broadcast_local(self, message: dict):
        """Отправка сообщения локально подключенным клиентам WebSockets текущего процесса"""
        for user_id in list(self.active_connections.keys()):
            for connection in list(self.active_connections.get(user_id, [])):
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def broadcast(self, message: dict):
        """Широковещательная отправка: локальным сокетам + публикация в Redis для других процессов"""
        # 1. Отправляем локальным клиентам процесса
        await self.broadcast_local(message)
        
        # 2. Публикуем в Redis Pub/Sub
        try:
            from app.core.redis import sync_redis_client
            envelope = {
                "sender_id": PROCESS_INSTANCE_ID,
                "data": dict(message)
            }
            await asyncio.to_thread(sync_redis_client.publish, REDIS_WS_CHANNEL, json.dumps(envelope, ensure_ascii=False))
        except Exception as e:
            logger.debug(f"Redis WS broadcast failed: {e}")

    def broadcast_sync(self, message: dict):
        """Потокобезопасная отправка broadcast из любого фонового треда, воркера Celery или синхронной функции"""
        # 1. Если есть локальные сокеты в текущем процессе
        if self.loop and self.loop.is_running() and self.active_connections:
            try:
                asyncio.run_coroutine_threadsafe(self.broadcast_local(message), self.loop)
            except Exception:
                pass
        
        # 2. Публикуем в Redis Pub/Sub через sync_redis_client (мгновенно уходит в FastAPI backend)
        try:
            from app.core.redis import sync_redis_client
            envelope = {
                "sender_id": PROCESS_INSTANCE_ID,
                "data": dict(message)
            }
            sync_redis_client.publish(REDIS_WS_CHANNEL, json.dumps(envelope, ensure_ascii=False))
        except Exception as err:
            logger.debug(f"sync_redis_client publish failed: {err}")

    async def start_redis_listener(self):
        """Фоновый слушатель сообщений из Redis Pub/Sub в FastAPI backend"""
        if self._listener_started:
            return
        self._listener_started = True
        
        from app.core.redis import REDIS_URL
        import redis.asyncio as aioredis
        
        while True:
            try:
                r = aioredis.from_url(REDIS_URL, decode_responses=True)
                pubsub = r.pubsub()
                await pubsub.subscribe(REDIS_WS_CHANNEL)
                logger.info(f"Subscribed to Redis WS broadcast channel: {REDIS_WS_CHANNEL}")
                
                async for msg in pubsub.listen():
                    if msg and msg.get("type") == "message":
                        raw_data = msg.get("data")
                        if raw_data:
                            try:
                                env = json.loads(raw_data)
                                if isinstance(env, dict) and env.get("sender_id") != PROCESS_INSTANCE_ID:
                                    data = env.get("data", {})
                                    if data and isinstance(data, dict):
                                        await self.broadcast_local(data)
                            except Exception as parse_err:
                                logger.error(f"Error parsing Redis WS message: {parse_err}")
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.warning(f"Redis WS listener connection error: {e}. Reconnecting in 3s...")
                await asyncio.sleep(3)

manager = ConnectionManager()

@router.get("/contacts", response_model=List[ChatContact])
def get_contacts(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Получение списка контактов для чата"""
    # Состояние прочтения общего чата для текущего пользователя
    read_state = db.get(ChatReadState, current_user.id)
    last_read_group_id = read_state.last_read_group_msg_id if read_state else 0
    
    # Количество непрочитанных в общем чате
    unread_group = db.exec(
        select(func.count(ChatMessage.id)).where(
            ChatMessage.is_group == True,
            ChatMessage.id > last_read_group_id
        )
    ).one()

    contacts = []
    # Добавляем "Общую группу" как первый контакт
    contacts.append(ChatContact(
        id=0,
        username="all",
        full_name="Общая группа",
        role_name="Все сотрудники",
        is_online=True,
        unread_count=unread_group
    ))

    # Оптимизированное получение непрочитанных для всех пользователей сразу
    unread_counts = db.exec(
        select(ChatMessage.sender_id, func.count(ChatMessage.id))
        .where(
            ChatMessage.receiver_id == current_user.id,
            ChatMessage.read_at == None,
            ChatMessage.is_group == False
        )
        .group_by(ChatMessage.sender_id)
    ).all()
    unread_map = {sender_id: count for sender_id, count in unread_counts}

    # Предварительная загрузка ролей для исключения N+1
    statement = select(User).where(User.is_active == True).options(joinedload(User.role))
    users = db.exec(statement).all()

    for user in users:
        if user.id == current_user.id:
            continue
            
        contacts.append(ChatContact(
            id=user.id,
            username=user.username,
            full_name=user.full_name,
            role_name=user.role.name if user.role else None,
            is_online=False, # Можно добавить логику онлайн статуса позже
            unread_count=unread_map.get(user.id, 0)
        ))
        
    return contacts

@router.get("/messages", response_model=ChatHistoryResponse)
def get_messages(
    receiver_id: Optional[int] = Query(None),
    is_group: bool = Query(False),
    limit: int = Query(50),
    offset: int = Query(0),
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Получение истории сообщений"""
    if is_group:
        statement = select(ChatMessage).where(ChatMessage.is_group == True)
    else:
        if receiver_id is None:
            raise HTTPException(status_code=400, detail="receiver_id is required for personal chat")
        statement = select(ChatMessage).where(
            or_(
                and_(ChatMessage.sender_id == current_user.id, ChatMessage.receiver_id == receiver_id),
                and_(ChatMessage.sender_id == receiver_id, ChatMessage.receiver_id == current_user.id)
            )
        )
    
    # Считаем общее количество для пагинации
    total_statement = select(func.count()).select_from(statement.subquery())
    total = db.exec(total_statement).one()
    
    # Получаем сообщения с пагинацией (новые в конце для фронта, поэтому берем последние и переворачиваем)
    statement = statement.order_by(desc(ChatMessage.created_at)).limit(limit).offset(offset)
    messages = db.exec(statement).all()
    
    # Получаем уникальные sender_id из сообщений
    sender_ids = {msg.sender_id for msg in messages}
    sender_map = {}
    if sender_ids:
        from app.schemas.user import UserRead
        senders = db.exec(select(User).where(User.id.in_(list(sender_ids)))).all()
        sender_map = {u.id: UserRead.model_validate(u) for u in senders}
    
    # Формируем ответ
    res_messages = []
    for msg in messages:
        msg_read = ChatMessageRead.model_validate(msg)
        msg_read.sender = sender_map.get(msg.sender_id)
        res_messages.append(msg_read)
        
    # Возвращаем в хронологическом порядке (старые в начале)
    return ChatHistoryResponse(messages=res_messages[::-1], total=total)

@router.post("/read")
def mark_as_read(
    request: ChatReadRequest,
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
):
    """Пометить сообщения как прочитанные"""
    if request.is_group:
        if request.last_msg_id is None:
            # Ищем ID самого последнего сообщения в группе
            last_msg = db.exec(select(ChatMessage).where(ChatMessage.is_group == True).order_by(desc(ChatMessage.id))).first()
            last_msg_id = last_msg.id if last_msg else 0
        else:
            last_msg_id = request.last_msg_id
            
        read_state = db.get(ChatReadState, current_user.id)
        if not read_state:
            read_state = ChatReadState(user_id=current_user.id, last_read_group_msg_id=last_msg_id)
            db.add(read_state)
        else:
            read_state.last_read_group_msg_id = max(read_state.last_read_group_msg_id, last_msg_id)
            read_state.updated_at = datetime.now(timezone.utc)
    else:
        if request.sender_id is None:
            return {"status": "ignored", "detail": "sender_id is required for personal chat mark_as_read"}
        
        sender_id = request.sender_id
        # Помечаем все сообщения от отправителя текущему пользователю как прочитанные
        db.exec(
            ChatMessage.__table__.update().where(
                ChatMessage.sender_id == sender_id,
                ChatMessage.receiver_id == current_user.id,
                ChatMessage.read_at == None
            ).values(read_at=datetime.now(timezone.utc))
        )
    
    db.commit()
    return {"status": "ok"}

def send_chat_push_notification(db: Session, sender_name: str, receiver_id: int, content: str, is_group: bool = False):
    """Отправляет пуш-уведомление получателю сообщения, если у него это включено"""
    try:
        from app.models.admin_notification_settings import AdminNotificationSettings
        from app.models.push_subscription import PushSubscription
        from app.core.webpush_utils import send_web_push
        from app.api.notifications import get_global_vapid_keys
        
        # Получаем личные настройки получателя
        settings_db = db.exec(select(AdminNotificationSettings).where(AdminNotificationSettings.user_id == receiver_id)).first()
        if settings_db and not settings_db.chat_message_push_enabled:
            return
            
        subscriptions = db.exec(select(PushSubscription).where(PushSubscription.user_id == receiver_id)).all()
        if not subscriptions:
            return
            
        _, vapid_priv = get_global_vapid_keys(db)
        
        title = f"Групповой чат" if is_group else f"Сообщение от {sender_name}"
        body = f"{sender_name}: {content}" if is_group else content
        if len(body) > 100:
            body = body[:97] + "..."
            
        payload_data = json.dumps({
            "title": title,
            "body": body,
            "icon": "/favicon.ico",
            "url": "/admin/mailings/cascades",
            "event_type": "chat_message"
        }, ensure_ascii=False)
        # Сохраняем уведомление в историю БД
        try:
            from app.models.admin_notification import AdminNotification
            db_notif = AdminNotification(
                user_id=receiver_id,
                title=title,
                body=body,
                url="/admin/mailings/cascades",
                event_type="chat_message",
                is_read=False
            )
            db.add(db_notif)
            db.commit()
        except Exception as db_err:
            print(f"Failed to log chat notification to database: {db_err}")

        db_changed = False
        for sub in subscriptions:
            sub_info = {
                "endpoint": sub.endpoint,
                "keys": {
                    "p256dh": sub.p256dh,
                    "auth": sub.auth
                }
            }
            res = send_web_push(sub_info, payload_data, vapid_priv)
            if res == "remove":
                db.delete(sub)
                db_changed = True
                
        if db_changed:
            db.commit()
    except Exception as e:
        print(f"Failed to send chat push notification: {e}")


@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: Optional[str] = Query(None)
):
    """WebSocket эндпоинт для чата и мультичата (без персистентного удержания подключения к БД)"""
    user_id = 0
    if token:
        try:
            from app.core.database import Session, engine
            with Session(engine) as db:
                user = deps.get_user_from_token(db, token)
                if user:
                    user_id = user.id
        except Exception as e:
            pass

    await manager.connect(user_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            action = message_data.get("action", "send")
            
            if action == "send":
                if not user_id:
                    continue

                content = message_data.get("content")
                receiver_id = message_data.get("receiver_id")
                is_group = message_data.get("is_group", False)
                
                if not content:
                    continue
                    
                msg_payload = None
                
                # Сохраняем в БД в короткоживущей сессии
                from app.core.database import Session, engine
                with Session(engine) as db:
                    current_user = db.get(User, user_id)
                    if not current_user:
                        continue

                    new_msg = ChatMessage(
                        sender_id=current_user.id,
                        receiver_id=receiver_id if not is_group else None,
                        is_group=is_group,
                        content=content,
                        created_at=datetime.now(timezone.utc)
                    )
                    db.add(new_msg)
                    db.commit()
                    db.refresh(new_msg)
                    
                    # Подготавливаем данные для отправки
                    from app.schemas.user import UserRead
                    sender_read = UserRead.model_validate(current_user)
                    payload = ChatMessageRead.model_validate(new_msg)
                    payload.sender = sender_read
                    
                    msg_payload = {
                        "type": "new_message",
                        "message": json.loads(payload.model_dump_json())
                    }
                    
                    # Отправка Push-уведомлений получателям
                    try:
                        sender_name = current_user.full_name or current_user.username or "Сотрудник"
                        if is_group:
                            # Находим всех активных пользователей, кроме отправителя
                            other_users = db.exec(select(User.id).where(User.id != current_user.id, User.is_active == True)).all()
                            for u_id in other_users:
                                send_chat_push_notification(db, sender_name, u_id, content, is_group=True)
                        else:
                            if receiver_id != current_user.id:
                                send_chat_push_notification(db, sender_name, receiver_id, content, is_group=False)
                    except Exception as push_err:
                        print(f"Chat push error: {push_err}")

                # Рассылаем по WebSockets после закрытия сессии БД
                if msg_payload:
                    if is_group:
                        await manager.broadcast(msg_payload)
                    else:
                        # Получателю
                        await manager.send_personal_message(msg_payload, receiver_id)
                        # Себе (на случай если открыто несколько вкладок)
                        if receiver_id != user_id:
                            await manager.send_personal_message(msg_payload, user_id)
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(user_id, websocket)
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(user_id, websocket)

