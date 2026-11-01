from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.message_log import CustomerMessageLog
from app.models.customer import Customer
from app.models.broadcast import CustomerBroadcast
from app.models.reminder import CustomerReminder
from app.schemas.mailing_cascade import CustomerMessageLogResponse

router = APIRouter(prefix="/mailings/logs", tags=["Message Logs"])

@router.get("", response_model=List[CustomerMessageLogResponse])
def get_logs(
    channel: Optional[str] = Query(None, description="Фильтр по каналу (vk, telegram, max, sms)"),
    status: Optional[str] = Query(None, description="Фильтр по статусу"),
    customer_id: Optional[int] = Query(None),
    limit: int = Query(50, le=100),
    offset: int = Query(0),
    db: Session = Depends(get_session)
):
    """
    Получить журнал отправленных сообщений.
    Возвращает обогащенную информацию об адресатах, рассылках и напоминаниях.
    """
    statement = select(
        CustomerMessageLog, 
        Customer.name, 
        CustomerBroadcast.title, 
        CustomerReminder.name
    )\
        .outerjoin(Customer, CustomerMessageLog.customer_id == Customer.id)\
        .outerjoin(CustomerBroadcast, CustomerMessageLog.broadcast_id == CustomerBroadcast.id)\
        .outerjoin(CustomerReminder, CustomerMessageLog.reminder_id == CustomerReminder.id)
        
    if channel:
        statement = statement.where(CustomerMessageLog.channel == channel)
    if status:
        statement = statement.where(CustomerMessageLog.status == status)
    if customer_id:
        statement = statement.where(CustomerMessageLog.customer_id == customer_id)
        
    statement = statement.order_by(CustomerMessageLog.id.desc())\
        .limit(limit).offset(offset)
        
    results = db.exec(statement).all()
    
    logs_list = []
    for log, cust_name, br_title, rem_name in results:
        logs_list.append(CustomerMessageLogResponse(
            id=log.id,
            customer_id=log.customer_id,
            order_id=log.order_id,
            broadcast_id=log.broadcast_id,
            reminder_id=log.reminder_id,
            cascade_step_id=log.cascade_step_id,
            channel=log.channel,
            recipient_address=log.recipient_address,
            text=log.text,
            status=log.status,
            message_id=log.message_id,
            error_text=log.error_text,
            sent_at=log.sent_at,
            delivered_at=log.delivered_at,
            read_at=log.read_at,
            clicked_at=log.clicked_at,
            created_at=getattr(log, 'created_at', None) or log.sent_at,
            customer_name=cust_name or "Гость",
            broadcast_title=br_title,
            reminder_name=rem_name
        ))
        
    return logs_list
