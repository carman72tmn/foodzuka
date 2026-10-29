from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.reminder import CustomerReminder
from app.models.mailing_cascade import MailingCascade
from app.schemas.mailing_cascade import (
    CustomerReminderCreate, 
    CustomerReminderUpdate, 
    CustomerReminderResponse
)
from datetime import datetime, timezone

router = APIRouter(prefix="/mailings/reminders", tags=["Customer Reminders"])

@router.get("", response_model=List[CustomerReminderResponse])
def get_reminders(db: Session = Depends(get_session)):
    """Получить список правил напоминаний"""
    statement = select(CustomerReminder, MailingCascade.name)\
        .outerjoin(MailingCascade, CustomerReminder.cascade_id == MailingCascade.id)\
        .order_by(CustomerReminder.days_inactive)
        
    results = db.exec(statement).all()
    
    reminders = []
    for rem, cascade_name in results:
        reminders.append(CustomerReminderResponse(
            id=rem.id,
            name=rem.name,
            days_inactive=rem.days_inactive,
            template=rem.template,
            cascade_id=rem.cascade_id,
            is_active=rem.is_active,
            created_at=rem.created_at,
            updated_at=rem.updated_at,
            cascade_name=cascade_name
        ))
    return reminders

@router.post("", response_model=CustomerReminderResponse)
def create_reminder(reminder_data: CustomerReminderCreate, db: Session = Depends(get_session)):
    """Создать новое напоминание"""
    reminder = CustomerReminder(**reminder_data.model_dump())
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    
    # Получаем имя каскада
    cascade_name = None
    if reminder.cascade_id:
        cascade = db.get(MailingCascade, reminder.cascade_id)
        if cascade:
            cascade_name = cascade.name
            
    return CustomerReminderResponse(
        id=reminder.id,
        name=reminder.name,
        days_inactive=reminder.days_inactive,
        template=reminder.template,
        cascade_id=reminder.cascade_id,
        is_active=reminder.is_active,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
        cascade_name=cascade_name
    )

@router.patch("/{reminder_id}", response_model=CustomerReminderResponse)
def update_reminder(
    reminder_id: int, 
    reminder_data: CustomerReminderUpdate, 
    db: Session = Depends(get_session)
):
    """Обновить настройки напоминания"""
    reminder = db.get(CustomerReminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    update_data = reminder_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(reminder, key, value)
        
    reminder.updated_at = datetime.now(timezone.utc)
    db.add(reminder)
    db.commit()
    db.refresh(reminder)
    
    # Получаем имя каскада
    cascade_name = None
    if reminder.cascade_id:
        cascade = db.get(MailingCascade, reminder.cascade_id)
        if cascade:
            cascade_name = cascade.name
            
    return CustomerReminderResponse(
        id=reminder.id,
        name=reminder.name,
        days_inactive=reminder.days_inactive,
        template=reminder.template,
        cascade_id=reminder.cascade_id,
        is_active=reminder.is_active,
        created_at=reminder.created_at,
        updated_at=reminder.updated_at,
        cascade_name=cascade_name
    )

@router.delete("/{reminder_id}")
def delete_reminder(reminder_id: int, db: Session = Depends(get_session)):
    """Удалить напоминание"""
    reminder = db.get(CustomerReminder, reminder_id)
    if not reminder:
        raise HTTPException(status_code=404, detail="Reminder not found")
        
    db.delete(reminder)
    db.commit()
    return {"success": True}
