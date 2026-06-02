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

router = APIRouter(prefix="/chat", tags=["chat"])

class ConnectionManager:
    def __init__(self):
        # user_id -> list of websockets
        self.active_connections: Dict[int, List[WebSocket]] = {}

    async def connect(self, user_id: int, websocket: WebSocket):
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
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

    async def broadcast(self, message: dict):
        for user_id in self.active_connections:
            for connection in self.active_connections[user_id]:
                try:
                    await connection.send_json(message)
                except Exception:
                    pass

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

@router.websocket("/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(deps.get_db)
):
    """WebSocket эндпоинт для чата"""
    try:
        user = deps.get_user_from_token(db, token)
    except Exception as e:
        print(f"WS Auth Error: {e}")
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await manager.connect(user.id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            message_data = json.loads(data)
            
            action = message_data.get("action", "send")
            
            if action == "send":
                content = message_data.get("content")
                receiver_id = message_data.get("receiver_id")
                is_group = message_data.get("is_group", False)
                
                if not content:
                    continue
                    
                # Сохраняем в БД
                new_msg = ChatMessage(
                    sender_id=user.id,
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
                sender_read = UserRead.model_validate(user)
                payload = ChatMessageRead.model_validate(new_msg)
                payload.sender = sender_read
                
                msg_payload = {
                    "type": "new_message",
                    "message": json.loads(payload.model_dump_json())
                }
                
                # Рассылаем
                if is_group:
                    await manager.broadcast(msg_payload)
                else:
                    # Получателю
                    await manager.send_personal_message(msg_payload, receiver_id)
                    # Себе (на случай если открыто несколько вкладок)
                    if receiver_id != user.id:
                        await manager.send_personal_message(msg_payload, user.id)
            
            elif action == "ping":
                await websocket.send_json({"type": "pong"})
                
    except WebSocketDisconnect:
        manager.disconnect(user.id, websocket)
    except Exception as e:
        print(f"WS Error: {e}")
        manager.disconnect(user.id, websocket)
