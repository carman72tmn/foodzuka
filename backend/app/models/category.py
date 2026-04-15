"""
Модель категории товаров
"""
from typing import Optional, List
from datetime import datetime
from sqlmodel import Field, SQLModel, Relationship


class Category(SQLModel, table=True):
    """Таблица категорий товаров"""
    __tablename__ = "categories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None)
    iiko_id: Optional[str] = Field(default=None, unique=True, index=True, max_length=255)

    # Иерархия
    parent_id: Optional[int] = Field(
        default=None,
        sa_column_kwargs={"nullable": True},
        foreign_key="categories.id"
    )

    # Изображения
    image_url: Optional[str] = Field(default=None, max_length=500)
    iiko_image_id: Optional[str] = Field(default=None, max_length=255)

    # Счётчики (обновляются при синхронизации)
    products_count: int = Field(default=0)
    modifiers_count: int = Field(default=0)

    sort_order: int = Field(default=0)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Пицца",
                "sort_order": 1,
                "is_active": True
            }
        }
