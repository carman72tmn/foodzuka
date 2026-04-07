"""
Модель типа оплаты iiko
"""
from typing import Optional
from datetime import datetime
from sqlmodel import Field, SQLModel


class PaymentType(SQLModel, table=True):
    """Таблица типов оплаты из iiko"""
    __tablename__ = "payment_types"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(max_length=255, index=True)
    iiko_id: str = Field(unique=True, index=True, max_length=255)
    kind: Optional[str] = Field(default=None, max_length=100)
    is_active: bool = Field(default=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Поля для сопоставления (mapping)
    # Например, если мы хотим связать iiko-оплату с нашим типом
    # mapping_code: Optional[str] = Field(default=None, max_length=100)

    class Config:
        """Настройки модели"""
        json_schema_extra = {
            "example": {
                "name": "Наличные",
                "iiko_id": "09342150-6101-492a-9cb0-39148d48a58a",
                "kind": "Cash",
                "is_active": True
            }
        }
