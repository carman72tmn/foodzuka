from datetime import datetime
from zoneinfo import ZoneInfo
import pytz

DEFAULT_TZ = ZoneInfo('Asia/Yekaterinburg')

def format_datetime(date_str: str) -> str:
    if not date_str:
        return '—'
    
    try:
        # Пытаемся распарсить ISO строку
        # Backend присылает 2024-04-16T12:00:00Z или +00:00
        if 'Z' in date_str:
            dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        else:
            dt = datetime.fromisoformat(date_str)
            
        # Если дата наивная (нет инфо о зоне), считаем что это UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=pytz.UTC)
            
        # Конвертируем в местное время
        local_dt = dt.astimezone(DEFAULT_TZ)
        
        return local_dt.strftime('%d.%m.%Y %H:%M')
    except Exception as e:
        print(f'Error formatting date {date_str}: {e}')
        return date_str
