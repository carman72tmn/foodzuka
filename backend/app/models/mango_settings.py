"""
Модели настроек интеграции с телефонией Mango Office (ВАТС) и журнала вызовов
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel


class MangoSettings(SQLModel, table=True):
    """Общие настройки подключения к API Mango Office ВАТС"""
    __tablename__ = "mango_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Реквизиты API
    vpbx_api_key: Optional[str] = Field(default=None, description="Уникальный код АТС (API Key)")
    vpbx_api_salt: Optional[str] = Field(default=None, description="Ключ для создания подписи (API Salt)")
    vpbx_url: str = Field(default="https://app.mango-office.ru/vpbx/", description="Базовый адрес API ВАТС")

    # Флаг активности интеграции
    is_active: bool = Field(default=False, description="Глобальный флаг активности интеграции с Mango Office")

    # Настройки по умолчанию
    default_extension: Optional[str] = Field(default=None, description="Внутренний номер сотрудника по умолчанию (например, 101)")
    auto_lookup_customer: bool = Field(default=True, description="Автоматический поиск клиента по номеру входящего звонка")
    create_customer_if_missing: bool = Field(default=False, description="Создавать гостя в базе, если номер не найден")
    notify_incoming_call: bool = Field(default=True, description="Показывать всплывающее уведомление о входящем звонке")
    recording_storage_mode: str = Field(default="stream", description="Режим аудио: stream (прокси) или direct")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)


class MangoCallLog(SQLModel, table=True):
    """Журнал входящих и исходящих звонков через Mango Office ВАТС"""
    __tablename__ = "mango_call_logs"

    id: Optional[int] = Field(default=None, primary_key=True)

    entry_id: Optional[str] = Field(default=None, index=True, description="Идентификатор цепочки вызова в Mango")
    call_id: Optional[str] = Field(default=None, index=True, description="Идентификатор звонка")
    call_state: Optional[str] = Field(default=None, description="Состояние вызова (Appeared, Connected, Disconnected, OnHold)")
    direction: str = Field(default="incoming", index=True, description="Направление: incoming (входящий) или outgoing (исходящий)")

    from_number: Optional[str] = Field(default=None, index=True, description="Номер звонящего абонента")
    from_extension: Optional[str] = Field(default=None, description="Внутренний добавочный номер звонящего")
    to_number: Optional[str] = Field(default=None, index=True, description="Номер вызываемого абонента")
    to_extension: Optional[str] = Field(default=None, description="Внутренний добавочный номер вызываемого")
    line_number: Optional[str] = Field(default=None, description="Внешний номер линии компании")

    status: str = Field(default="active", index=True, description="Статус вызова: success (отвечен), missed (пропущен), busy (занято), active (в процессе), failed (ошибка)")
    disconnect_reason: Optional[str] = Field(default=None, description="Причина завершения звонка")

    duration_wait: int = Field(default=0, description="Время ожидания ответа в секундах")
    duration_talk: int = Field(default=0, description="Время разговора в секундах")

    recording_id: Optional[str] = Field(default=None, index=True, description="Идентификатор записи разговора в Mango")
    recording_url: Optional[str] = Field(default=None, description="Прямая ссылка или путь к записи")

    # Связи с CRM
    customer_id: Optional[int] = Field(default=None, index=True, description="Ссылка на клиента в таблице customers")
    customer_name: Optional[str] = Field(default=None, description="ФИО клиента")
    order_id: Optional[int] = Field(default=None, description="Ссылка на заказ")
    comment: Optional[str] = Field(default=None, description="Примечание к звонку")
    raw_data: Optional[str] = Field(default=None, description="Сырые данные события от Mango в JSON")

    # Временные метки
    started_at: Optional[datetime] = Field(default=None, description="Время поступления звонка")
    connected_at: Optional[datetime] = Field(default=None, description="Время соединения с оператором")
    ended_at: Optional[datetime] = Field(default=None, description="Время завершения вызова")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
