"""
Модели для модуля "Закуп" (версия 2.0)
"""
from typing import Optional, List, TYPE_CHECKING
import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel, Relationship

if TYPE_CHECKING:
    from app.models.user import User



class Supplier(SQLModel, table=True):
    """Справочник поставщиков товаров/услуг"""
    __tablename__ = "suppliers"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    phone: Optional[str] = Field(default=None, max_length=50)
    email: Optional[str] = Field(default=None, max_length=100)
    comment: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=utc_now)
    updated_at: datetime.datetime = Field(default_factory=utc_now)

    # Связь с позициями
    positions: List["PurchasePosition"] = Relationship(back_populates="supplier")
class PurchaseSubcategory(SQLModel, table=True):
    """Справочник подкатегорий закупа"""
    __tablename__ = "purchase_subcategories"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, unique=True, index=True)
    created_at: datetime.datetime = Field(default_factory=utc_now)


class PurchasePosition(SQLModel, table=True):
    """Справочник позиций (товаров/услуг) для закупа"""
    __tablename__ = "purchase_positions"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    category: str = Field(max_length=50, index=True)  # 'supply' (поставки), 'shop' (магазин), 'household' (хозка)
    subcategory: Optional[str] = Field(default=None, max_length=255, index=True) # молочка, овощи, крупы и т.д.
    unit: Optional[str] = Field(default="шт", max_length=50)
    supplier_id: Optional[int] = Field(default=None, foreign_key="suppliers.id")
    is_active: bool = Field(default=True)
    created_at: datetime.datetime = Field(default_factory=utc_now)
    updated_at: datetime.datetime = Field(default_factory=utc_now)

    # Связи
    supplier: Optional[Supplier] = Relationship(back_populates="positions")
    list_items: List["PurchaseListItem"] = Relationship(
        back_populates="position",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class PurchaseList(SQLModel, table=True):
    """Заголовки списков закупа (на конкретную дату по направлениям)"""
    __tablename__ = "purchase_lists"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255)
    category: str = Field(max_length=50, index=True) # 'supply', 'shop', 'household'
    date: datetime.date = Field(index=True) # дата поставки
    status: str = Field(default="draft", index=True) # 'draft' (черновик), 'sent' (отправлен)
    created_by_id: Optional[int] = Field(default=None, foreign_key="users.id", nullable=True)
    updated_by_id: Optional[int] = Field(default=None, foreign_key="users.id", nullable=True)
    created_at: datetime.datetime = Field(default_factory=utc_now)
    updated_at: datetime.datetime = Field(default_factory=utc_now)

    # Элементы списка
    items: List["PurchaseListItem"] = Relationship(
        back_populates="purchase_list",
        sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )

    # Связи с пользователями (создатель / редактор)
    created_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={"primaryjoin": "PurchaseList.created_by_id == User.id"}
    )
    updated_by: Optional["User"] = Relationship(
        sa_relationship_kwargs={"primaryjoin": "PurchaseList.updated_by_id == User.id"}
    )

    @property
    def items_count(self) -> int:
        if not self.items:
            return 0
        return len([item for item in self.items if item.quantity > 0])


class PurchaseListItem(SQLModel, table=True):
    """Элементы списков закупа (количества товаров)"""
    __tablename__ = "purchase_list_items"

    id: Optional[int] = Field(default=None, primary_key=True)
    list_id: int = Field(foreign_key="purchase_lists.id")
    position_id: int = Field(foreign_key="purchase_positions.id")
    quantity: float = Field(default=0.0)
    comment: Optional[str] = Field(default=None)
    is_urgent: bool = Field(default=False)
    is_bought: bool = Field(default=False)
    created_at: datetime.datetime = Field(default_factory=utc_now)
    updated_at: datetime.datetime = Field(default_factory=utc_now)

    # Связи
    purchase_list: Optional[PurchaseList] = Relationship(back_populates="items")
    position: Optional[PurchasePosition] = Relationship(back_populates="list_items")


class PurchaseListChange(SQLModel, table=True):
    """Лог изменений списков закупа"""
    __tablename__ = "purchase_list_changes"

    id: Optional[int] = Field(default=None, primary_key=True)
    list_id: int = Field(foreign_key="purchase_lists.id")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", nullable=True)
    action_type: str = Field(max_length=50) # 'create', 'update_meta', 'update_items', 'send', 'toggle_bought'
    details: Optional[str] = Field(default=None)
    created_at: datetime.datetime = Field(default_factory=utc_now)

    # Связи
    user: Optional["User"] = Relationship()


# Разрешение циклических ссылок в Pydantic v2
PurchaseList.model_rebuild()
PurchaseListItem.model_rebuild()
PurchasePosition.model_rebuild()
PurchaseListChange.model_rebuild()
