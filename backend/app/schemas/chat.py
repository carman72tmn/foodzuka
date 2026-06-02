from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from .user import UserRead

class ChatMessageBase(BaseModel):
    content: str
    receiver_id: Optional[int] = None
    is_group: bool = False
    type: str = "text"

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessageRead(ChatMessageBase):
    id: int
    sender_id: int
    created_at: datetime
    read_at: Optional[datetime] = None
    sender: Optional[UserRead] = None
    
    model_config = ConfigDict(from_attributes=True)

class ChatContact(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    role_name: Optional[str] = None
    last_login_at: Optional[datetime] = None
    is_online: bool = False
    unread_count: int = 0

class ChatHistoryResponse(BaseModel):
    messages: List[ChatMessageRead]
    total: int

class ChatReadRequest(BaseModel):
    sender_id: Optional[int] = None
    is_group: bool = False
    last_msg_id: Optional[int] = None
