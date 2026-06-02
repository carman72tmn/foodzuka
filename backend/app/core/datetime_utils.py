from datetime import datetime, timezone
import zoneinfo
from typing import Optional
from sqlmodel import Session, select

def utc_now():
    """Возвращает текущее время в UTC с информацией о часовом поясе"""
    return datetime.now(timezone.utc)

def get_tz_name(session: Session) -> str:
    """Получает имя часового пояса из настроек БД или возвращает дефолт"""
    from app.models.iiko_settings import IikoSettings
    settings = session.exec(select(IikoSettings)).first()
    if settings:
        tz_n = settings.timezone_name or settings.manual_timezone
        if tz_n:
            # Исправление для некорректных символов (например, 'एशिया/Tyumen')
            if "Tyumen" in tz_n: return "Asia/Tyumen"
            if "Yekaterinburg" in tz_n: return "Asia/Yekaterinburg"
            if "Moscow" in tz_n: return "Europe/Moscow"
            return tz_n
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

def get_day_boundaries(date_str: str, tz_name: str):
    """
    date_str: YYYY-MM-DD
    Возвращает (start_utc, end_utc) для данного дня в указанном часовом поясе.
    """
    tz = zoneinfo.ZoneInfo(tz_name)
    dt = datetime.strptime(date_str, "%Y-%m-%d")
    
    start_local = dt.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=tz)
    end_local = dt.replace(hour=23, minute=59, second=59, microsecond=999999, tzinfo=tz)
    
    # Переводим в UTC и убираем tzinfo для сравнения с naive datetime в БД
    start_utc = start_local.astimezone(timezone.utc).replace(tzinfo=None)
    end_utc = end_local.astimezone(timezone.utc).replace(tzinfo=None)
    
    return start_utc, end_utc
