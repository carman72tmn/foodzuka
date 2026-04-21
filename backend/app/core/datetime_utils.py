from datetime import datetime, timezone
import zoneinfo
from typing import Optional
from sqlmodel import Session, select
from app.models.iiko_settings import IikoSettings

def utc_now():
    """Возвращает текущее время в UTC с информацией о часовом поясе"""
    return datetime.now(timezone.utc)

def get_tz_name(session: Session) -> str:
    """Получает имя часового пояса из настроек БД или возвращает дефолт"""
    settings = session.exec(select(IikoSettings)).first()
    if settings:
        if settings.timezone_name:
            return settings.timezone_name
        if settings.manual_timezone:
            # Преобразование GMT+5 в что-то понятное zoneinfo если нужно, 
            # но обычно timezone_name заполнен (Europe/Moscow, Asia/Yekaterinburg)
            return settings.manual_timezone
    return "Asia/Yekaterinburg"

def get_tz(session: Session) -> zoneinfo.ZoneInfo:
    """Возвращает объект часового пояса на основе настроек"""
    return zoneinfo.ZoneInfo(get_tz_name(session))

def to_local(dt: datetime, tz_name: str) -> datetime:
    """Переводит время в локальный часовой пояс"""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(zoneinfo.ZoneInfo(tz_name))

def get_local_now(tz_name: str) -> datetime:
    """Возвращает текущее локальное время"""
    return datetime.now(zoneinfo.ZoneInfo(tz_name))
