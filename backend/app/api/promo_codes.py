"""
API эндпоинты для управления промокодами
"""
import json
import random
import string
from typing import List, Optional
from datetime import datetime, date, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.promo_code import PromoCode

router = APIRouter(prefix="/promo-codes", tags=["Promo Codes"])


# ============= Pydantic Schemas =============

class PromoCodeCreate(BaseModel):
    name: str = Field(max_length=255)
    code: str = Field(max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    promo_type: str = Field(pattern="^(percent|fixed|gift|free_items|funnel)$")
    discount_value: Decimal = Field(default=0, ge=0)
    gift_product_ids: Optional[str] = None
    usage_type: str = Field(default="multi", pattern="^(multi|single|single_per_user)$")
    max_uses: Optional[int] = Field(default=None, ge=1)
    no_combine: bool = False
    first_order_only: bool = False
    min_order_amount: Optional[Decimal] = Field(default=None, ge=0)
    min_items_count: Optional[int] = Field(default=None, ge=1)
    required_product_ids: Optional[str] = None
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None
    time_from: Optional[str] = None
    time_until: Optional[str] = None
    valid_days: Optional[str] = None
    platforms: Optional[str] = None
    delivery_types: Optional[str] = None
    branch_ids: Optional[str] = None


class PromoCodeResponse(PromoCodeCreate):
    id: int
    current_uses: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MassGenerateRequest(BaseModel):
    """Массовая генерация промокодов по шаблону"""
    prefix: str = Field(max_length=20, description="Префикс кода")
    count: int = Field(ge=1, le=1000, description="Кол-во промокодов")
    code_length: int = Field(default=8, ge=4, le=20)
    # Все остальные поля как у PromoCodeCreate (кроме code)
    name: str = Field(max_length=255)
    description: Optional[str] = None
    promo_type: str = Field(pattern="^(percent|fixed|gift|free_items|funnel)$")
    discount_value: Decimal = Field(default=0, ge=0)
    usage_type: str = "single"
    valid_from: Optional[date] = None
    valid_until: Optional[date] = None


# ============= CRUD =============

@router.get("/", response_model=List[PromoCodeResponse])
async def list_promo_codes(
    promo_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    limit: int = Query(default=100, le=500),
    session: Session = Depends(get_session)
):
    """Список промокодов с фильтрами"""
    query = select(PromoCode).order_by(PromoCode.created_at.desc()).limit(limit)
    if promo_type:
        query = query.where(PromoCode.promo_type == promo_type)
    if is_active is not None:
        query = query.where(PromoCode.is_active == is_active)
    if search:
        query = query.where(
            PromoCode.code.contains(search) | PromoCode.name.contains(search)
        )
    return session.exec(query).all()


@router.get("/{promo_id}", response_model=PromoCodeResponse)
async def get_promo_code(
    promo_id: int,
    session: Session = Depends(get_session)
):
    """Получить промокод по ID"""
    promo = session.get(PromoCode, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    return promo


@router.post("/", response_model=PromoCodeResponse)
async def create_promo_code(
    data: PromoCodeCreate,
    session: Session = Depends(get_session)
):
    """Создать промокод"""
    # Проверяем уникальность кода
    existing = session.exec(
        select(PromoCode).where(PromoCode.code == data.code)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail=f"Code '{data.code}' already exists")

    promo = PromoCode(**data.model_dump())
    session.add(promo)
    session.commit()
    session.refresh(promo)
    return promo


@router.put("/{promo_id}", response_model=PromoCodeResponse)
async def update_promo_code(
    promo_id: int,
    data: PromoCodeCreate,
    session: Session = Depends(get_session)
):
    """Обновить промокод"""
    promo = session.get(PromoCode, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    for key, value in data.model_dump().items():
        setattr(promo, key, value)
    promo.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(promo)
    return promo


@router.delete("/{promo_id}")
async def delete_promo_code(
    promo_id: int,
    session: Session = Depends(get_session)
):
    """Удалить промокод"""
    promo = session.get(PromoCode, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    session.delete(promo)
    session.commit()
    return {"success": True}


# ============= Действия =============

@router.post("/{promo_id}/toggle")
async def toggle_promo_code(
    promo_id: int,
    session: Session = Depends(get_session)
):
    """Активировать/деактивировать промокод"""
    promo = session.get(PromoCode, promo_id)
    if not promo:
        raise HTTPException(status_code=404, detail="Promo code not found")
    promo.is_active = not promo.is_active
    promo.updated_at = datetime.now(timezone.utc)
    session.commit()
    return {"success": True, "is_active": promo.is_active}


@router.post("/{promo_id}/duplicate", response_model=PromoCodeResponse)
async def duplicate_promo_code(
    promo_id: int,
    session: Session = Depends(get_session)
):
    """Копировать промокод"""
    original = session.get(PromoCode, promo_id)
    if not original:
        raise HTTPException(status_code=404, detail="Promo code not found")

    # Генерируем уникальный код
    suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    new_code = f"{original.code}_COPY_{suffix}"

    copy = PromoCode(
        name=f"{original.name} (копия)",
        code=new_code,
        description=original.description,
        promo_type=original.promo_type,
        discount_value=original.discount_value,
        gift_product_ids=original.gift_product_ids,
        usage_type=original.usage_type,
        max_uses=original.max_uses,
        no_combine=original.no_combine,
        first_order_only=original.first_order_only,
        min_order_amount=original.min_order_amount,
        min_items_count=original.min_items_count,
        required_product_ids=original.required_product_ids,
        valid_from=original.valid_from,
        valid_until=original.valid_until,
        time_from=original.time_from,
        time_until=original.time_until,
        valid_days=original.valid_days,
        platforms=original.platforms,
        delivery_types=original.delivery_types,
        branch_ids=original.branch_ids,
        is_active=False  # Копия неактивна по умолчанию
    )
    session.add(copy)
    session.commit()
    session.refresh(copy)
    return copy


# ============= Массовая генерация =============

@router.post("/mass-generate", response_model=List[PromoCodeResponse])
async def mass_generate(
    data: MassGenerateRequest,
    session: Session = Depends(get_session)
):
    """Массовая генерация промокодов по шаблону"""
    generated = []

    for i in range(data.count):
        # Генерируем уникальный код
        while True:
            suffix = ''.join(
                random.choices(string.ascii_uppercase + string.digits, k=data.code_length)
            )
            code = f"{data.prefix}{suffix}"
            existing = session.exec(
                select(PromoCode).where(PromoCode.code == code)
            ).first()
            if not existing:
                break

        promo = PromoCode(
            name=f"{data.name} #{i + 1}",
            code=code,
            description=data.description,
            promo_type=data.promo_type,
            discount_value=data.discount_value,
            usage_type=data.usage_type,
            valid_from=data.valid_from,
            valid_until=data.valid_until,
            is_active=True
        )
        session.add(promo)
        generated.append(promo)

    session.commit()
    for p in generated:
        session.refresh(p)

    return generated
