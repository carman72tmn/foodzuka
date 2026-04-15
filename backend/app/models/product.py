"""
Модель товара/продукта
"""
from typing import Optional
from datetime import datetime
from decimal import Decimal
from sqlmodel import Field, SQLModel, Relationship, Column, JSON
from sqlalchemy import Numeric

class ProductSize(SQLModel, table=True):
    """Таблица размеров товара (например, 25см, 30см, 35см)"""
    __tablename__ = "product_sizes"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    iiko_id: str = Field(index=True, max_length=255)
    name: str = Field(max_length=255)
    price: Decimal = Field(sa_type=Numeric(10, 2))
    is_default: bool = Field(default=False)
    updated_at: Optional[datetime] = Field(default=None)
    
    product: "Product" = Relationship(back_populates="sizes")

class ProductModifierGroup(SQLModel, table=True):
    """Группа модификаторов товара (например, 'Топпинги', 'Основа')"""
    __tablename__ = "product_modifier_groups"

    id: Optional[int] = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="products.id", index=True)
    iiko_id: str = Field(index=True, max_length=255)
    name: str = Field(max_length=255)
    min_amount: int = Field(default=0)
    max_amount: int = Field(default=1)
    is_required: bool = Field(default=False)
    
    product: "Product" = Relationship(back_populates="modifier_groups")
    modifiers: list["ProductModifier"] = Relationship(
        back_populates="group",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class ProductModifier(SQLModel, table=True):
    """Конкретный модификатор в группе (например, 'Сырный бортик', 'Халапеньо')"""
    __tablename__ = "product_modifiers"

    id: Optional[int] = Field(default=None, primary_key=True)
    group_id: int = Field(foreign_key="product_modifier_groups.id", index=True)
    iiko_id: str = Field(index=True, max_length=255)
    name: str = Field(max_length=255)
    price: Decimal = Field(sa_type=Numeric(10, 2))
    default_amount: int = Field(default=0)
    min_amount: int = Field(default=0)
    max_amount: int = Field(default=1)
    
    group: "ProductModifierGroup" = Relationship(back_populates="modifiers")


class Product(SQLModel, table=True):
    """Таблица товаров"""
    __tablename__ = "products"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    description: Optional[str] = Field(default=None)
    price: Decimal = Field(sa_type=Numeric(10, 2))
    image_url: Optional[str] = Field(default=None, max_length=500)
    category_id: Optional[int] = Field(default=None, foreign_key="categories.id")
    iiko_id: Optional[str] = Field(default=None, unique=True, index=True, max_length=255)
    iiko_image_id: Optional[str] = Field(default=None, max_length=255)
    article: Optional[str] = Field(default=None, index=True, max_length=100)
    is_available: bool = Field(default=True)
    sort_order: int = Field(default=0)
    
    # Новые поля для каталога
    weight_grams: Optional[int] = Field(default=None)
    volume_ml: Optional[int] = Field(default=None)
    calories: Optional[int] = Field(default=None)
    proteins: Optional[float] = Field(default=None)
    fats: Optional[float] = Field(default=None)
    carbohydrates: Optional[float] = Field(default=None)
    
    # Маркетинг
    is_popular: bool = Field(default=False)
    old_price: Optional[Decimal] = Field(default=None, sa_type=Numeric(10, 2))
    max_discount_percent: Optional[int] = Field(default=None, description="Максимальная скидка в %")
    bonus_accrual_percent: Optional[int] = Field(default=None, description="% начисления бонусов")
    
    # Синхронизация стоп-листов (список branch_ids)
    stop_list_branch_ids: list[int] = Field(default=[], sa_column=Column(JSON))

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    sizes: list[ProductSize] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )
    modifier_groups: list[ProductModifierGroup] = Relationship(
        back_populates="product",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    class Config:
        """Настройки модели"""
        json_schema_extra = {
            "example": {
                "name": "Маргарита",
                "description": "Классическая пицца с моцареллой и томатами",
                "price": 450.00,
                "category_id": 1,
                "is_available": True
            }
        }
