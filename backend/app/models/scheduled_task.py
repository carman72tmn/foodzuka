"""
Модель для управления запланированными задачами (APScheduler)
"""
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel, JSON
import json

class ScheduledTask(SQLModel, table=True):
    """Метаданные запланированной задачи для управления из админки"""
    __tablename__ = "scheduled_tasks"

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str = Field(description="Понятное название задачи (напр. Синхронизация меню)")
    task_name: str = Field(description="Путь к функции задачи (напр. app.tasks.general_tasks.sync_menu_task)")
    
    # Параметры вызова
    args: Optional[str] = Field(default="[]", description="Аргументы в формате JSON")
    kwargs: Optional[str] = Field(default="{}", description="Именованные аргументы в формате JSON")
    
    # Настройки триггера
    trigger_type: str = Field(description="Тип триггера: interval, cron, dependency")
    trigger_value: str = Field(description="Значение триггера (JSON для интервала или строка для cron)")
    
    # Статус и управление
    is_active: bool = Field(default=True, description="Включена ли задача")
    job_id: Optional[str] = Field(default=None, index=True, description="ID задачи в APScheduler")
    
    # История и зависимости
    last_run: Optional[datetime] = Field(default=None, description="Время последнего запуска")
    next_run: Optional[datetime] = Field(default=None, description="Время следующего запуска")
    trigger_after_job_id: Optional[str] = Field(default=None, description="Запустить после завершения указанной задачи")
    
    description: Optional[str] = Field(default=None, description="Описание задачи")
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    def get_args(self) -> List[Any]:
        return json.loads(self.args or "[]")

    def get_kwargs(self) -> Dict[str, Any]:
        return json.loads(self.kwargs or "{}")

    def get_trigger_params(self) -> Dict[str, Any]:
        try:
            return json.loads(self.trigger_value)
        except:
            return {"expression": self.trigger_value}
