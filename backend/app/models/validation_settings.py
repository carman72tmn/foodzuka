"""
Модели настроек сервисов валидации номеров телефонов
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel

class ValidationSettings(SQLModel, table=True):
    """Настройки верификации телефонов и API провайдеров (например, RedSMS)"""
    __tablename__ = "validation_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Общие флаги
    is_active: bool = Field(default=False, description="Глобальный флаг активности проверки номеров")
    provider: str = Field(default="red_sms", description="Идентификатор провайдера (red_sms)")

    # Настройки API (RedSMS)
    api_login: Optional[str] = Field(default=None, description="Логин API провайдера")
    api_key: Optional[str] = Field(default=None, description="Ключ API (пароль)")
    sender_name: Optional[str] = Field(default="REDSMS", description="Имя отправителя для SMS")
    
    # Wait Call настройки
    wait_call_num: Optional[str] = Field(default=None, description="Авторизационный номер телефона для Wait Call")
    wait_call_no_voice: bool = Field(default=False, description="Для Wait Call не озвучивать код (сбрасывать звонок после соединения)")

    # Каналы отправки
    active_route: str = Field(default="sms", description="Активный канал отправки (sms, voice, wcall, fcall, cascade)")
    cascade_routes: str = Field(default="fcall,voice,sms", description="Список каналов для каскадной отправки (через запятую)")
    cascade_delay: int = Field(default=30, description="Задержка между каналами в секундах")

    # ВКонтакте верификация
    vk_verification_method: str = Field(default="none", description="Метод верификации ВК (none, mini_app, lead_form)")
    vk_mini_app_id: Optional[int] = Field(default=None, description="ID мини-приложения ВК")
    vk_mini_app_secret: Optional[str] = Field(default=None, description="Защищенный ключ мини-приложения ВК")
    vk_lead_form_url: Optional[str] = Field(default=None, description="Ссылка на Lead-форму ВК")
    
    # Текстовые сообщения и шаги для ВК-бота верификации
    vk_alternative_methods: str = Field(default="fcall,wcall,tg,max", description="Список разрешенных альтернативных каналов (через запятую)")
    vk_msg_start: Optional[str] = Field(default=None, description="Текст начала проверки (для Mini App / Lead Form)")
    vk_msg_choose_method: Optional[str] = Field(default=None, description="Текст выбора альтернативного метода")
    vk_msg_fcall_prompt: Optional[str] = Field(default=None, description="Текст запроса телефона для Flash Call")
    vk_msg_fcall_code: Optional[str] = Field(default=None, description="Текст запроса кода Flash Call")
    vk_msg_wcall_prompt: Optional[str] = Field(default=None, description="Текст запроса телефона для Wait Call")
    vk_msg_wcall_instruct: Optional[str] = Field(default=None, description="Текст инструкции для Wait Call")
    vk_msg_tg_instruct: Optional[str] = Field(default=None, description="Текст перехода в Telegram")
    vk_msg_max_instruct: Optional[str] = Field(default=None, description="Текст перехода в МАКС")
    vk_msg_success: Optional[str] = Field(default=None, description="Текст успешного подтверждения")
    vk_msg_error_code: Optional[str] = Field(default=None, description="Текст ошибки неверного кода")

    # Telegram бот для клиентов
    telegram_bot_token: Optional[str] = Field(default=None, description="Токен Telegram-бота для клиентов")
    telegram_bot_username: Optional[str] = Field(default=None, description="Имя пользователя Telegram-бота (без @)")

    # МАКС бот для клиентов
    max_bot_token: Optional[str] = Field(default=None, description="Токен МАКС-бота для клиентов")
    max_bot_username: Optional[str] = Field(default=None, description="Имя пользователя МАКС-бота (без @)")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)
