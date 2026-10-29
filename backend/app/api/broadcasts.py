from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.broadcast import CustomerBroadcast
from app.models.mailing_cascade import MailingCascade
from app.schemas.mailing_cascade import (
    CustomerBroadcastCreate, 
    CustomerBroadcastUpdate, 
    CustomerBroadcastResponse
)
from datetime import datetime, timezone

router = APIRouter(prefix="/mailings/broadcasts", tags=["Customer Broadcasts"])

@router.get("", response_model=List[CustomerBroadcastResponse])
def get_broadcasts(db: Session = Depends(get_session)):
    """Получить список рассылок"""
    statement = select(CustomerBroadcast, MailingCascade.name)\
        .outerjoin(MailingCascade, CustomerBroadcast.cascade_id == MailingCascade.id)\
        .order_by(CustomerBroadcast.created_at.desc())
        
    results = db.exec(statement).all()
    
    broadcasts = []
    for br, cascade_name in results:
        broadcasts.append(CustomerBroadcastResponse(
            id=br.id,
            title=br.title,
            template_text=br.template_text,
            cascade_id=br.cascade_id,
            audience_filters=br.audience_filters,
            status=br.status,
            scheduled_at=br.scheduled_at,
            sent_count=br.sent_count,
            delivered_count=br.delivered_count,
            read_count=br.read_count,
            error_count=br.error_count,
            created_at=br.created_at,
            updated_at=br.updated_at,
            cascade_name=cascade_name
        ))
    return broadcasts

@router.post("", response_model=CustomerBroadcastResponse)
def create_broadcast(broadcast_data: CustomerBroadcastCreate, db: Session = Depends(get_session)):
    """Создать новую рассылку"""
    broadcast = CustomerBroadcast(**broadcast_data.model_dump())
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)
    
    # Получаем имя каскада
    cascade_name = None
    if broadcast.cascade_id:
        cascade = db.get(MailingCascade, broadcast.cascade_id)
        if cascade:
            cascade_name = cascade.name
            
    return CustomerBroadcastResponse(
        id=broadcast.id,
        title=broadcast.title,
        template_text=broadcast.template_text,
        cascade_id=broadcast.cascade_id,
        audience_filters=broadcast.audience_filters,
        status=broadcast.status,
        scheduled_at=broadcast.scheduled_at,
        sent_count=broadcast.sent_count,
        delivered_count=broadcast.delivered_count,
        read_count=broadcast.read_count,
        error_count=broadcast.error_count,
        created_at=broadcast.created_at,
        updated_at=broadcast.updated_at,
        cascade_name=cascade_name
    )

@router.patch("/{broadcast_id}", response_model=CustomerBroadcastResponse)
def update_broadcast(
    broadcast_id: int, 
    broadcast_data: CustomerBroadcastUpdate, 
    db: Session = Depends(get_session)
):
    """Обновить рассылку"""
    broadcast = db.get(CustomerBroadcast, broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
        
    update_data = broadcast_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(broadcast, key, value)
        
    broadcast.updated_at = datetime.now(timezone.utc)
    db.add(broadcast)
    db.commit()
    db.refresh(broadcast)
    
    # Получаем имя каскада
    cascade_name = None
    if broadcast.cascade_id:
        cascade = db.get(MailingCascade, broadcast.cascade_id)
        if cascade:
            cascade_name = cascade.name
            
    return CustomerBroadcastResponse(
        id=broadcast.id,
        title=broadcast.title,
        template_text=broadcast.template_text,
        cascade_id=broadcast.cascade_id,
        audience_filters=broadcast.audience_filters,
        status=broadcast.status,
        scheduled_at=broadcast.scheduled_at,
        sent_count=broadcast.sent_count,
        delivered_count=broadcast.delivered_count,
        read_count=broadcast.read_count,
        error_count=broadcast.error_count,
        created_at=broadcast.created_at,
        updated_at=broadcast.updated_at,
        cascade_name=cascade_name
    )

@router.post("/{broadcast_id}/send")
def send_broadcast(broadcast_id: int, db: Session = Depends(get_session)):
    """Запустить рассылку немедленно в фоновом режиме через Celery"""
    broadcast = db.get(CustomerBroadcast, broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
        
    if broadcast.status == "processing":
        raise HTTPException(status_code=400, detail="Broadcast is already processing")
        
    broadcast.status = "processing"
    db.add(broadcast)
    db.commit()
    
    # Запуск Celery-задачи
    from app.tasks.mailing_tasks import execute_customer_broadcast_task
    execute_customer_broadcast_task.delay(broadcast_id)
    
    return {"status": "processing", "message": "Рассылка запущена в фоновом режиме"}

@router.delete("/{broadcast_id}")
def delete_broadcast(broadcast_id: int, db: Session = Depends(get_session)):
    """Удалить рассылку"""
    broadcast = db.get(CustomerBroadcast, broadcast_id)
    if not broadcast:
        raise HTTPException(status_code=404, detail="Broadcast not found")
        
    db.delete(broadcast)
    db.commit()
    return {"success": True}
