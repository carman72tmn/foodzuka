"""
Модель пользователя (для админ-панели и API аутентификации)
"""
from typing import Optional, TYPE_CHECKING
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from .role import Role
    from .employee import Employee



class User(SQLModel, table=True):
    """Таблица пользователей системы"""
    __tablename__ = "users"

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, index=True, max_length=100)
    email: str = Field(unique=True, index=True, max_length=255)
    hashed_password: str = Field(max_length=255)
    full_name: Optional[str] = Field(default=None, max_length=255)
    is_active: bool = Field(default=True)
    is_superuser: bool = Field(default=False)
    
    # Новые поля для RBAC и интеграции с iiko
    role_id: Optional[int] = Field(default=None, foreign_key="roles.id")
    iiko_id: Optional[str] = Field(default=None, unique=True, index=True) # ID сотрудника в iiko
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

    # Связи
    role: Optional["Role"] = Relationship(back_populates="users")
    
    # Связь с сотрудником iiko
    employee: Optional["Employee"] = Relationship(
        sa_relationship_kwargs={"primaryjoin": "foreign(User.iiko_id) == Employee.iiko_id", "uselist": False}
    )

    class Config:
        """Настройки модели"""
        json_schema_extra = {
            "example": {
                "username": "admin",
                "email": "admin@foodtech.com",
                "full_name": "Administrator",
                "is_active": True,
                "is_superuser": True
            }
        }
