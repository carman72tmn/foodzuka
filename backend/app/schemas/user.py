from typing import Optional, List, Any, Annotated
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, ConfigDict, field_validator, BeforeValidator

def transform_uuid_to_str(v: Any) -> Optional[str]:
    if v is None: return None
    return str(v)

IikoId = Annotated[Optional[str], BeforeValidator(transform_uuid_to_str)]

class PermissionRead(BaseModel):
    id: int
    name: str
    code: str
    model_config = ConfigDict(from_attributes=True)

class RoleRead(BaseModel):
    id: int
    name: str
    code: Optional[str] = None
    iiko_id: IikoId = None
    is_system: bool = False
    default_page: Optional[str] = None
    permissions: List[PermissionRead] = []
    model_config = ConfigDict(from_attributes=True)

class RoleCreate(BaseModel):
    name: str
    code: Optional[str] = None
    description: Optional[str] = None
    default_page: Optional[str] = None

class RoleUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    default_page: Optional[str] = None

class RolePermissionUpdate(BaseModel):
    permission_ids: List[int]

class UserBase(BaseModel):
    username: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: bool = True
    role_id: Optional[int] = None
    iiko_id: IikoId = None
    profile_data: Optional[dict] = None
    vk_user_id: Optional[int] = None

class UserCreate(UserBase):
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    role_id: Optional[int] = None
    iiko_id: IikoId = None
    password: Optional[str] = None
    profile_data: Optional[dict] = None
    vk_user_id: Optional[int] = None

class EmployeeShort(BaseModel):
    id: int
    iiko_id: IikoId = None
    name: str
    role: Optional[str] = None
    is_courier: bool = False
    model_config = ConfigDict(from_attributes=True)

class UserRead(UserBase):
    id: int
    is_superuser: bool
    is_courier: bool = False
    created_at: datetime
    updated_at: datetime
    last_login_at: Optional[datetime] = None
    role: Optional[RoleRead] = None
    employee: Optional[EmployeeShort] = None
    model_config = ConfigDict(from_attributes=True)
