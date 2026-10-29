from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.bot_command import BotCommand
from app.core.datetime_utils import utc_now

router = APIRouter(prefix="/bot-commands", tags=["Bot Commands"])

@router.get("/", response_model=List[BotCommand])
def get_bot_commands(db: Session = Depends(get_session)):
    """Получить список всех команд ботов"""
    commands = db.exec(select(BotCommand).order_by(BotCommand.id)).all()
    return commands

@router.post("/", response_model=BotCommand)
def create_bot_command(command: BotCommand, db: Session = Depends(get_session)):
    """Создать новую команду бота"""
    # Удаляем id, чтобы он сгенерировался через sequence
    command_data = command.model_dump(exclude={"id", "created_at", "updated_at"})
    db_command = BotCommand(**command_data)
    db.add(db_command)
    db.commit()
    db.refresh(db_command)
    return db_command

@router.put("/{command_id}", response_model=BotCommand)
def update_bot_command(command_id: int, command_data: BotCommand, db: Session = Depends(get_session)):
    """Обновить настройки команды бота"""
    db_command = db.get(BotCommand, command_id)
    if not db_command:
        raise HTTPException(status_code=404, detail="Command not found")
    
    update_dict = command_data.model_dump(exclude={"id", "created_at", "updated_at"})
    for key, value in update_dict.items():
        setattr(db_command, key, value)
    
    db_command.updated_at = utc_now()
    db.add(db_command)
    db.commit()
    db.refresh(db_command)
    return db_command

@router.delete("/{command_id}")
def delete_bot_command(command_id: int, db: Session = Depends(get_session)):
    """Удалить команду бота"""
    db_command = db.get(BotCommand, command_id)
    if not db_command:
        raise HTTPException(status_code=404, detail="Command not found")
    
    # Защитим команду 100 от удаления
    if db_command.id == 100:
        raise HTTPException(status_code=400, detail="Cannot delete default system command")
        
    db.delete(db_command)
    db.commit()
    return {"success": True}
