"""
API эндпоинты для программы лояльности
"""
from typing import List, Optional
from datetime import datetime, timezone
from decimal import Decimal
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field, ConfigDict
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.loyalty import LoyaltyStatus, LoyaltyRule, LoyaltyTransaction

router = APIRouter(prefix="/loyalty", tags=["Loyalty Program"])


# ============= Pydantic Schemas =============

class LoyaltyStatusCreate(BaseModel):
    name: str = Field(max_length=100)
    max_discount: Decimal = Field(default=0, ge=0, le=100)
    min_status_points: int = Field(default=0, ge=0)
    sort_order: int = 0
    is_active: bool = True


class LoyaltyStatusResponse(LoyaltyStatusCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LoyaltyRuleCreate(BaseModel):
    title: str = Field(max_length=255)
    loyalty_status_id: int
    rule_type: str = "cashback"
    cashback_percent: Decimal = Field(default=0, ge=0, le=100)
    bonus_ttl_days: int = Field(default=0, ge=0)
    status_ttl_days: int = Field(default=0, ge=0)
    is_active: bool = True


class LoyaltyRuleResponse(LoyaltyRuleCreate):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LoyaltyTransactionCreate(BaseModel):
    transaction_type: str = Field(pattern="^(credit|debit)$")
    phone: str = Field(max_length=50)
    points: Decimal = Field(gt=0)
    ttl_days: int = Field(default=0, ge=0)
    comment: Optional[str] = None
    order_id: Optional[int] = None


class LoyaltyTransactionResponse(LoyaltyTransactionCreate):
    id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============= Статусы =============

@router.get("/statuses", response_model=List[LoyaltyStatusResponse])
async def list_statuses(session: Session = Depends(get_session)):
    """Получить все статусы лояльности"""
    return session.exec(
        select(LoyaltyStatus).order_by(LoyaltyStatus.sort_order)
    ).all()


@router.post("/statuses", response_model=LoyaltyStatusResponse)
async def create_status(
    data: LoyaltyStatusCreate,
    session: Session = Depends(get_session)
):
    """Создать статус лояльности"""
    status = LoyaltyStatus(**data.model_dump())
    session.add(status)
    session.commit()
    session.refresh(status)
    return status


@router.put("/statuses/{status_id}", response_model=LoyaltyStatusResponse)
async def update_status(
    status_id: int,
    data: LoyaltyStatusCreate,
    session: Session = Depends(get_session)
):
    """Обновить статус лояльности"""
    status = session.get(LoyaltyStatus, status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    for key, value in data.model_dump().items():
        setattr(status, key, value)
    status.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(status)
    return status


@router.delete("/statuses/{status_id}")
async def delete_status(
    status_id: int,
    session: Session = Depends(get_session)
):
    """Удалить статус лояльности"""
    status = session.get(LoyaltyStatus, status_id)
    if not status:
        raise HTTPException(status_code=404, detail="Status not found")
    session.delete(status)
    session.commit()
    return {"success": True}


# ============= Правила =============

@router.get("/rules", response_model=List[LoyaltyRuleResponse])
async def list_rules(session: Session = Depends(get_session)):
    """Получить все правила"""
    return session.exec(select(LoyaltyRule)).all()


@router.post("/rules", response_model=LoyaltyRuleResponse)
async def create_rule(
    data: LoyaltyRuleCreate,
    session: Session = Depends(get_session)
):
    """Создать правило"""
    rule = LoyaltyRule(**data.model_dump())
    session.add(rule)
    session.commit()
    session.refresh(rule)
    return rule


@router.put("/rules/{rule_id}", response_model=LoyaltyRuleResponse)
async def update_rule(
    rule_id: int,
    data: LoyaltyRuleCreate,
    session: Session = Depends(get_session)
):
    """Обновить правило"""
    rule = session.get(LoyaltyRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    for key, value in data.model_dump().items():
        setattr(rule, key, value)
    rule.updated_at = datetime.now(timezone.utc)
    session.commit()
    session.refresh(rule)
    return rule


@router.delete("/rules/{rule_id}")
async def delete_rule(
    rule_id: int,
    session: Session = Depends(get_session)
):
    """Удалить правило"""
    rule = session.get(LoyaltyRule, rule_id)
    if not rule:
        raise HTTPException(status_code=404, detail="Rule not found")
    session.delete(rule)
    session.commit()
    return {"success": True}


# ============= Транзакции =============

@router.get("/transactions", response_model=List[LoyaltyTransactionResponse])
async def list_transactions(
    phone: Optional[str] = None,
    limit: int = 100,
    session: Session = Depends(get_session)
):
    """Получить транзакции (с фильтром по телефону)"""
    query = select(LoyaltyTransaction).order_by(
        LoyaltyTransaction.created_at.desc()
    ).limit(limit)
    if phone:
        query = query.where(LoyaltyTransaction.phone == phone)
    return session.exec(query).all()


from app.tasks.customer_tasks import sync_single_customer_task
import logging

logger = logging.getLogger(__name__)

@router.post("/transactions", response_model=LoyaltyTransactionResponse)
async def create_transaction(
    data: LoyaltyTransactionCreate,
    session: Session = Depends(get_session)
):
    """Создать транзакцию (зачисление/списание) и синхронизировать клиента"""
    tx = LoyaltyTransaction(**data.model_dump())
    session.add(tx)
    session.commit()
    session.refresh(tx)
    
    # Запускаем фоновую синхронизацию, так как баланс изменился
    try:
        sync_single_customer_task.delay(data.phone)
    except Exception as e:
        logger.warning(f"Failed to trigger sync after transaction for {data.phone}: {e}")
        
    return tx


@router.get("/balance/{phone}")
async def get_balance(phone: str, session: Session = Depends(get_session)):
    """Получить баланс бонусов клиента по телефону"""
    transactions = session.exec(
        select(LoyaltyTransaction).where(
            LoyaltyTransaction.phone == phone
        )
    ).all()

    balance = sum(
        tx.points if tx.transaction_type == "credit" else -tx.points
        for tx in transactions
    )
    return {
        "phone": phone,
        "balance": float(balance),
        "transactions_count": len(transactions)
    }
