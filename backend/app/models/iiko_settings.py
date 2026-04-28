"""
Модель настроек интеграции с iiko
"""
from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel


class IikoSettings(SQLModel, table=True):
    """Настройки подключения к iiko Cloud API"""
    __tablename__ = "iiko_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Основные настройки подключения
    api_login: str = Field(max_length=500, description="API Login Cloud API key")
    organization_id: Optional[str] = Field(
        default=None, max_length=255,
        description="UUID выбранной организации"
    )
    external_menu_id: Optional[str] = Field(
        default=None, max_length=255,
        description="ID внешнего меню для выгрузки"
    )
    terminal_group_id: Optional[str] = Field(
        default=None, max_length=255,
        description="UUID терминальной группы"
    )
    price_category_id: Optional[str] = Field(
        default=None, max_length=255,
        description="UUID выбранной категории цен для выгрузки меню"
    )


    # Типы оплаты
    payment_type_cash: Optional[str] = Field(
        default=None, max_length=255,
        description="ID типа оплаты — наличные"
    )
    payment_type_card: Optional[str] = Field(
        default=None, max_length=255,
        description="ID типа оплаты — карта"
    )
    payment_type_online: Optional[str] = Field(
        default=None, max_length=255,
        description="ID типа оплаты — онлайн"
    )
    payment_type_bonus: Optional[str] = Field(
        default=None, max_length=255,
        description="ID типа оплаты — бонусные баллы"
    )

    # Бонусная система
    bonus_limit_percent: int = Field(
        default=0,
        description="Лимит списания баллов в % от суммы заказа (0-100)"
    )
    discount_id: Optional[str] = Field(
        default=None, max_length=255,
        description="Идентификатор универсальной скидки"
    )

    # Флаги
    no_pass_promo: bool = Field(
        default=False,
        description="Не передавать промокоды из Result.Rest в iiko"
    )
    no_use_bonus: bool = Field(
        default=False,
        description="Не использовать бонусные баллы"
    )
    no_use_iiko_promo: bool = Field(
        default=False,
        description="Не использовать промокоды из iiko"
    )

    # Резервные каналы для ошибок
    fallback_email: Optional[str] = Field(
        default=None, max_length=255,
        description="Email для уведомлений при ошибках передачи заказа"
    )
    fallback_telegram_id: Optional[str] = Field(
        default=None, max_length=100,
        description="Telegram ID для уведомлений при ошибках"
    )

    # Вебхуки (iiko Cloud API push notifications)
    webhook_url: Optional[str] = Field(
        default=None, max_length=500,
        description="URL для приема вебхуков (напр. https://domain.com/api/v1/webhooks/iiko)"
    )
    webhook_auth_token: Optional[str] = Field(
        default=None, max_length=255,
        description="Токен авторизации для вебхуков (Authorization header)"
    )

    # Настройки iiko Resto (Direct Office API)
    resto_url: Optional[str] = Field(
        default=None, max_length=500,
        description="URL сервера iiko Resto (напр. https://domain.iiko.it/resto)"
    )
    resto_login: Optional[str] = Field(
        default=None, max_length=255,
        description="Логин для iiko Resto API"
    )
    resto_password: Optional[str] = Field(
        default=None, max_length=255,
        description="Пароль для iiko Resto API"
    )

    # Настройки POS Loyalty Server
    pos_loyalty_name: Optional[str] = Field(
        default=None, max_length=255,
        description="Наименование (pos_login) для Loyalty Server"
    )
    pos_loyalty_login: Optional[str] = Field(
        default=None, max_length=255,
        description="Логин для Loyalty Server"
    )
    pos_loyalty_password: Optional[str] = Field(
        default=None, max_length=255,
        description="Пароль для Loyalty Server"
    )
    pos_loyalty_channel: Optional[str] = Field(
        default=None, max_length=255,
        description="Канал подключения для Loyalty Server"
    )

    # Настройки управления (Дополнительно)
    address_format: str = Field(
        default="components", max_length=50,
        description="Формат парсинга адреса: components (по полям) или line1 (строка)"
    )
    city_name: Optional[str] = Field(
        default=None, max_length=100,
        description="Название города для автоматической настройки часового пояса"
    )
    manual_timezone: Optional[str] = Field(
        default=None, max_length=50,
        description="Ручная настройка часового пояса (GMT+X)"
    )
    timezone_name: Optional[str] = Field(
        default=None, max_length=100,
        description="Внутреннее имя часового пояса (напр. Europe/Moscow)"
    )

    delivery_zones_map_url: Optional[str] = Field(
        default=None, max_length=1000,
        description="Ссылка на карту Google (KML/GeoJSON) для импорта геометрии зон"
    )

    last_order_revision: int = Field(
        default=0,
        description="Номер последней успешно обработанной ревизии заказов"
    )

    # Метаданные
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
