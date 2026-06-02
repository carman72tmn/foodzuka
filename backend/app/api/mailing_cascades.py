from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.mailing_cascade import MailingCascade, MailingCascadeStep
from app.schemas import (
    MailingCascadeCreate, 
    MailingCascadeUpdate, 
    MailingCascadeResponse
)
from datetime import datetime, timezone

router = APIRouter(prefix="/mailings/cascades", tags=["Mailing Cascades"])

@router.get("/", response_model=List[MailingCascadeResponse])
def get_cascades(db: Session = Depends(get_session)):
    """Получить список всех каскадов"""
    cascades = db.exec(select(MailingCascade).order_by(MailingCascade.id.desc())).all()
    return cascades

@router.post("/", response_model=MailingCascadeResponse)
def create_cascade(cascade: MailingCascadeCreate, db: Session = Depends(get_session)):
    """Создать новый каскад с шагами"""
    db_cascade = MailingCascade(
        name=cascade.name,
        trigger_event=cascade.trigger_event,
        is_active=cascade.is_active
    )
    db.add(db_cascade)
    db.commit()
    db.refresh(db_cascade)

    # Добавляем шаги
    for i, step_data in enumerate(cascade.steps):
        db_step = MailingCascadeStep(
            **step_data.model_dump(),
            cascade_id=db_cascade.id,
            priority=i # Используем индекс как приоритет по умолчанию если не задан
        )
        db.add(db_step)
    
    db.commit()
    db.refresh(db_cascade)
    return db_cascade

@router.get("/{cascade_id}", response_model=MailingCascadeResponse)
def get_cascade(cascade_id: int, db: Session = Depends(get_session)):
    """Получить детали каскада"""
    cascade = db.get(MailingCascade, cascade_id)
    if not cascade:
        raise HTTPException(status_code=404, detail="Cascade not found")
    return cascade

@router.patch("/{cascade_id}", response_model=MailingCascadeResponse)
def update_cascade(cascade_id: int, cascade_data: MailingCascadeUpdate, db: Session = Depends(get_session)):
    """Обновить настройки каскада и его шаги"""
    db_cascade = db.get(MailingCascade, cascade_id)
    if not db_cascade:
        raise HTTPException(status_code=404, detail="Cascade not found")
        
    update_data = cascade_data.model_dump(exclude_unset=True)
    
    # Обновляем основные поля
    if "name" in update_data: db_cascade.name = update_data["name"]
    if "trigger_event" in update_data: db_cascade.trigger_event = update_data["trigger_event"]
    if "is_active" in update_data: db_cascade.is_active = update_data["is_active"]
    
    db_cascade.updated_at = datetime.now(timezone.utc)
    
    # Если переданы шаги - полностью заменяем их (проще для реализации в админке)
    if "steps" in update_data:
        # Удаляем старые шаги
        for step in db_cascade.steps:
            db.delete(step)
        
        # Добавляем новые
        for i, step_data in enumerate(update_data["steps"]):
            db_step = MailingCascadeStep(
                **step_data,
                cascade_id=db_cascade.id,
                priority=i
            )
            db.add(db_step)
            
    db.add(db_cascade)
    db.commit()
    db.refresh(db_cascade)
    return db_cascade

@router.delete("/{cascade_id}")
def delete_cascade(cascade_id: int, db: Session = Depends(get_session)):
    """Удалить каскад"""
    cascade = db.get(MailingCascade, cascade_id)
    if not cascade:
        raise HTTPException(status_code=404, detail="Cascade not found")
    
    db.delete(cascade)
    db.commit()
    return {"success": True}
