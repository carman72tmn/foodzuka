"""
Модель лога синхронизации
"""
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class SyncLog(SQLModel, table=True):
    """Лог операций синхронизации с iiko"""
    __tablename__ = "sync_logs"

    id: Optional[int] = Field(default=None, primary_key=True)
    sync_type: str = Field(
        max_length=50, index=True,
        description="Тип синхронизации: menu, prices, stop_lists, orders"
    )
    status: str = Field(
        max_length=20, index=True,
        description="Статус: running, success, error, partial"
    )
    categories_count: int = Field(
        default=0,
        description="Количество обработанных категорий"
    )
    products_count: int = Field(
        default=0,
        description="Количество обработанных товаров"
    )
    processed_count: int = Field(
        default=0,
        description="Количество обработанных объектов (заказов и т.д.)"
    )
    details: Optional[str] = Field(
        default=None,
        description="Детали операции / сообщение об ошибке"
    )
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class SyncStatus(SQLModel, table=True):
    """Статус выполнения фоновой задачи синхронизации"""
    __tablename__ = "sync_statuses"

    id: Optional[int] = Field(default=None, primary_key=True)
    task_id: str = Field(index=True, description="ID задачи Celery")
    sync_type: str = Field(index=True, description="Тип синхронизации (например, customers)")
    total_count: int = Field(default=0, description="Всего объектов для обработки")
    processed_count: int = Field(default=0, description="Обработано объектов")
    added_count: int = Field(default=0, description="Количество добавленных объектов")
    updated_count: int = Field(default=0, description="Количество обновленных объектов")
    status: str = Field(default="running", description="Статус: running, completed, error, cancelled")
    is_paused: bool = Field(default=False, description="Флаг паузы")
    is_cancelled: bool = Field(default=False, description="Флаг отмены")
    details: Optional[str] = Field(default=None, description="Детали операции")
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
