from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict

class PermissionRead(BaseModel):
    id: int
    name: str
    code: str
    model_config = ConfigDict(from_attributes=True)

class RoleRead(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    iiko_id: Optional[str] = None
    permissions: List[PermissionRead] = []
    model_config = ConfigDict(from_attributes=True)

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    role_id: Optional[int] = None
    iiko_id: Optional[str] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None
    iiko_id: Optional[str] = None
    password: Optional[str] = None

class UserRead(UserBase):
    id: int
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    role: Optional[RoleRead] = None
    model_config = ConfigDict(from_attributes=True)
