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
            if "Tyumen" in tz_n: return "Asia/Yekaterinburg"
            if "Yekaterinburg" in tz_n: return "Asia/Yekaterinburg"
            if "Moscow" in tz_n: return "Europe/Moscow"
            
            # Поддержка GMT/UTC смещений (например, "GMT +5:00", "UTC+3")
            import re
            m = re.match(r'^(?:GMT|UTC)\s*([+-])\s*(\d+)(?::(\d+))?$', tz_n.strip())
            if m:
                sign = m.group(1)
                hours = int(m.group(2))
                # В Etc/GMT знак противоположен смещению
                opp_sign = "-" if sign == "+" else "+"
                return f"Etc/GMT{opp_sign}{hours}"
                
            return tz_n
    return "Asia/Yekaterinburg"

def get_tz(session: Session) -> zoneinfo.ZoneInfo:
    """Возвращает объект часового пояса на основе настроек"""
    return zoneinfo.ZoneInfo(get_tz_name(session))

def to_local(dt: datetime, tz_name: str) -> datetime:
    """Переводит время в локальный часовой пояс"""
    if not tz_name or tz_name == "Asia/Tyumen" or "Tyumen" in tz_name:
        tz_name = "Asia/Yekaterinburg"
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    try:
        return dt.astimezone(zoneinfo.ZoneInfo(tz_name))
    except Exception:
        return dt.astimezone(zoneinfo.ZoneInfo("Asia/Yekaterinburg"))

def get_local_now(tz_name: str) -> datetime:
    """Возвращает текущее локальное время"""
    if not tz_name or tz_name == "Asia/Tyumen" or "Tyumen" in tz_name:
        tz_name = "Asia/Yekaterinburg"
    try:
        return datetime.now(zoneinfo.ZoneInfo(tz_name))
    except Exception:
        return datetime.now(zoneinfo.ZoneInfo("Asia/Yekaterinburg"))

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
