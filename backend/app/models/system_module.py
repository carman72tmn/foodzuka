from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel
from app.core.datetime_utils import utc_now

class SystemModule(SQLModel, table=True):
    __tablename__ = "system_modules"

    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True, max_length=100, description="Код модуля (slug)")
    name: str = Field(max_length=255, description="Название модуля")
    description: Optional[str] = Field(default=None, description="Описание модуля")
    version: str = Field(default="1.0.0", max_length=50, description="Версия модуля")
    author: Optional[str] = Field(default="FoodTech", max_length=100, description="Автор / Разработчик")
    is_enabled: bool = Field(default=True, description="Активен ли модуль")
    is_system: bool = Field(default=False, description="Системный защищенный модуль")
    icon: Optional[str] = Field(default="bx-extension", max_length=100, description="Иконка модуля")
    route_path: Optional[str] = Field(default=None, max_length=255, description="Маршрут в админ-панели")
    category: Optional[str] = Field(default="general", max_length=50, description="Категория модуля")
    settings_json: Optional[str] = Field(default="{}", description="JSON настроек модуля")
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
