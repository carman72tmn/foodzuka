"""
Модели ролей и прав доступа для системы RBAC
"""
from typing import List, Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .user import User



class RolePermissionLink(SQLModel, table=True):
    """Связь ролей и прав (многие-ко-многим)"""
    __tablename__ = "role_permission_links"

    role_id: Optional[int] = Field(
        default=None, foreign_key="roles.id", primary_key=True
    )
    permission_id: Optional[int] = Field(
        default=None, foreign_key="permissions.id", primary_key=True
    )


class Permission(SQLModel, table=True):
    """Таблица прав доступа"""
    __tablename__ = "permissions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    code: str = Field(unique=True, index=True, max_length=100)  # Например: orders_view
    description: Optional[str] = Field(default=None, max_length=255)
    category: str = Field(default="Общее", max_length=100)  # Для группировки в UI

    # Связи
    roles: List["Role"] = Relationship(back_populates="permissions", link_model=RolePermissionLink)


class Role(SQLModel, table=True):
    """Таблица ролей пользователей (включая должности из iiko)"""
    __tablename__ = "roles"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=100)
    code: Optional[str] = Field(default=None, unique=True, index=True, max_length=100)
    description: Optional[str] = Field(default=None, max_length=255)
    iiko_id: Optional[str] = Field(default=None, unique=True, index=True)  # ID должности из iiko
    is_system: bool = Field(default=False)  # Системные роли нельзя удалять
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Связи
    permissions: List[Permission] = Relationship(back_populates="roles", link_model=RolePermissionLink)
    users: List["User"] = Relationship(back_populates="role")
