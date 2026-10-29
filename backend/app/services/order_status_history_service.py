"""
Сервис управления историей изменения статусов заказа (лента событий).
Обеспечивает точный расчет времени пребывания в каждом статусе,
учет часового пояса организации и фиксацию закрытия/отмены заказов.
"""
from datetime import datetime, timezone
import zoneinfo
from typing import Optional, Dict, Any, List, Union
from sqlalchemy.orm.attributes import flag_modified
from sqlmodel import Session

from app.models.order import Order, OrderStatus
from app.core.datetime_utils import get_tz


STATUS_TITLES: Dict[str, str] = {
    "new": "Заказ принят",
    "unconfirmed": "Принят (Ожидает подтверждения)",
    "waitapproval": "Ожидает подтверждения",
    "confirmed": "Подтвержден",
    "accepted": "Подтвержден",
    "waitcooking": "Подтвержден (Передан кухне)",
    "readyforcooking": "Подтвержден",
    "preparing": "В сборке",
    "cooking": "Готовится",
    "cookingstarted": "Готовится",
    "assembling": "На сборке",
    "ready": "Готов",
    "cookingfinished": "Готов",
    "cookingcompleted": "Готов",
    "waiting": "Готов (Ожидает курьера)",
    "ready_for_pickup": "Готов к выдаче",
    "readyforpickup": "Готов к выдаче",
    "delivering": "У курьера",
    "onway": "У курьера",
    "delivered": "Доставлен",
    "closed": "Закрыт",
    "cancelled": "Отменен",
}


def get_status_title(status: Union[str, OrderStatus]) -> str:
    """Возвращает понятное название статуса на русском языке"""
    if isinstance(status, OrderStatus):
        s_key = status.value.lower()
    else:
        s_key = str(status or "").strip().lower()
    return STATUS_TITLES.get(s_key, s_key.capitalize() if s_key else "Принят")


def format_duration(seconds: int) -> str:
    """
    Форматирует секунды в читаемую строку на русском:
    - 45 сек
    - 15 мин
    - 1 ч 20 мин
    """
    if seconds < 0:
        seconds = 0
    if seconds < 60:
        return f"{seconds} сек"

    mins = seconds // 60
    if mins < 60:
        rem_sec = seconds % 60
        if rem_sec > 0 and mins < 5:
            return f"{mins} мин {rem_sec} сек"
        return f"{mins} мин"

    hours = mins // 60
    rem_mins = mins % 60
    if rem_mins > 0:
        return f"{hours} ч {rem_mins} мин"
    return f"{hours} ч"


def parse_iso_time(time_str: str, default_tz: zoneinfo.ZoneInfo) -> datetime:
    """Безопасно парсит ISO строку времени с учетом таймзоны"""
    try:
        dt = datetime.fromisoformat(time_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            return dt.replace(tzinfo=default_tz)
        return dt.astimezone(default_tz)
    except Exception:
        return datetime.now(default_tz)


def ensure_tz_aware(dt: Optional[datetime], target_tz: zoneinfo.ZoneInfo) -> datetime:
    """Приводит datetime к целевой таймзоне"""
    if not dt:
        return datetime.now(target_tz)
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc).astimezone(target_tz)
    return dt.astimezone(target_tz)


def append_order_status_history(
    order: Order,
    new_status: Union[str, OrderStatus],
    session: Optional[Session] = None,
    comment: Optional[str] = None,
    user: Optional[str] = None,
    custom_time: Optional[datetime] = None,
    tz: Optional[zoneinfo.ZoneInfo] = None
) -> None:
    """
    Добавляет статус в историю заказа с расчетом времени пребывания
    в предыдущем статусе и сохранением в локальном часовом поясе.
    """
    # 1. Определение целевого часового пояса
    target_tz = tz
    if not target_tz:
        if session:
            try:
                target_tz = get_tz(session)
            except Exception:
                target_tz = zoneinfo.ZoneInfo("Asia/Yekaterinburg")
        else:
            target_tz = zoneinfo.ZoneInfo("Asia/Yekaterinburg")

    now_tz = ensure_tz_aware(custom_time, target_tz)

    # 2. Нормализация статуса
    if isinstance(new_status, OrderStatus):
        new_status_str = new_status.value.lower()
    else:
        new_status_str = str(new_status or "").strip().lower()

    if not new_status_str:
        return

    history: List[Dict[str, Any]] = [dict(h) for h in (order.status_history or [])]

    # 3. Если история пустая - создаем начальную запись о создании/принятии заказа
    if not history:
        created_dt = order.iiko_creation_time or order.created_at
        created_tz = ensure_tz_aware(created_dt, target_tz)

        if new_status_str not in ("new", "unconfirmed", "waitapproval"):
            initial_diff_sec = max(0, int((now_tz - created_tz).total_seconds()))
            first_entry = {
                "status": "new",
                "title": "Заказ принят",
                "time": created_tz.isoformat(),
                "comment": "Заказ принят в обработку",
                "user": "System",
                "duration_seconds": initial_diff_sec,
                "duration_text": format_duration(initial_diff_sec)
            }
            history.append(first_entry)
        else:
            entry = {
                "status": new_status_str,
                "title": get_status_title(new_status_str),
                "time": created_tz.isoformat(),
                "comment": comment or "Заказ принят",
                "user": user or "System"
            }
            history.append(entry)
            order.status_history = history
            flag_modified(order, "status_history")
            return

    # 4. Проверяем предыдущую запись в истории
    if history:
        prev = history[-1]
        prev_status_str = str(prev.get("status", "")).strip().lower()

        # Если статус совпадает - не дублируем
        if prev_status_str == new_status_str:
            if comment and not prev.get("comment"):
                prev["comment"] = comment
                order.status_history = history
                flag_modified(order, "status_history")
            return

        # Рассчитываем время пребывания в предыдущем статусе
        prev_time_str = prev.get("time")
        if prev_time_str:
            prev_time_dt = parse_iso_time(prev_time_str, target_tz)
            duration_sec = max(0, int((now_tz - prev_time_dt).total_seconds()))
            prev["duration_seconds"] = duration_sec
            prev["duration_text"] = format_duration(duration_sec)

    # 5. Формируем новую запись для перехода в new_status
    new_entry: Dict[str, Any] = {
        "status": new_status_str,
        "title": get_status_title(new_status_str),
        "time": now_tz.isoformat(),
        "comment": comment,
        "user": user
    }

    # 6. Если статус терминальный (Закрыт / Отменен) - останавливаем учет времени
    if new_status_str in ("closed", "cancelled"):
        new_entry["is_terminal"] = True
        if history:
            first_time_str = history[0].get("time")
            if first_time_str:
                first_dt = parse_iso_time(first_time_str, target_tz)
                total_duration_sec = max(0, int((now_tz - first_dt).total_seconds()))
                new_entry["total_duration_seconds"] = total_duration_sec
                new_entry["total_duration_text"] = format_duration(total_duration_sec)

    history.append(new_entry)
    order.status_history = history
    flag_modified(order, "status_history")