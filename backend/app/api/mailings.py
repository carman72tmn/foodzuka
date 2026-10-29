from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.mailing import Mailing
from app.schemas import MailingCreate, MailingUpdate, MailingResponse

router = APIRouter(prefix="/mailings", tags=["Mailings"])

@router.get("", response_model=List[MailingResponse])
def get_mailings(db: Session = Depends(get_session)):
    """Получить список всех рассылок"""
    mailings = db.exec(select(Mailing).order_by(Mailing.id.desc())).all()
    return mailings

@router.post("", response_model=MailingResponse)
def create_mailing(mailing: MailingCreate, db: Session = Depends(get_session)):
    """Создать новую рассылку"""
    db_mailing = Mailing.model_validate(mailing)
    db.add(db_mailing)
    db.commit()
    db.refresh(db_mailing)
    return db_mailing

@router.get("/{mailing_id}", response_model=MailingResponse)
def get_mailing(mailing_id: int, db: Session = Depends(get_session)):
    """Получить информацию о конкретной рассылке"""
    mailing = db.get(Mailing, mailing_id)
    if not mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
    return mailing

@router.patch("/{mailing_id}", response_model=MailingResponse)
def update_mailing(mailing_id: int, mailing_data: MailingUpdate, db: Session = Depends(get_session)):
    """Обновить настройки рассылки"""
    db_mailing = db.get(Mailing, mailing_id)
    if not db_mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
        
    update_data = mailing_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_mailing, key, value)
        
    db.add(db_mailing)
    db.commit()
    db.refresh(db_mailing)
    return db_mailing

@router.post("/{mailing_id}/test")
def test_mailing(mailing_id: int, phone: str, db: Session = Depends(get_session)):
    """Отправить тестовое сообщение из рассылки на указанный номер (Заглушка)"""
    db_mailing = db.get(Mailing, mailing_id)
    if not db_mailing:
        raise HTTPException(status_code=404, detail="Mailing not found")
        
    # В реальности тут будет код отправки через сервис СМС/Телеграм бота
    return {"success": True, "message": f"Test message for {db_mailing.title} sent to {phone}"}
