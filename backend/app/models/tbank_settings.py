"""
Модели настроек интеграции с Т-Банком (T-API)
"""
from typing import Optional
from datetime import datetime
from app.core.datetime_utils import utc_now
from sqlmodel import Field, SQLModel

class TBankSettings(SQLModel, table=True):
    """Общие настройки подключения к API Т-Банка (Terminal Key, Token, Certificate)"""
    __tablename__ = "tbank_settings"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Настройки API
    terminal_key: Optional[str] = Field(default=None, description="Терминальный ключ (Terminal Key)")
    token: Optional[str] = Field(default=None, description="Токен API (Token)")
    certificate_content: Optional[str] = Field(default=None, description="Содержимое SSL-сертификата (PEM)")
    selected_terminals: Optional[str] = Field(default=None, description="Список выбранных Terminal Key торгового эквайринга в JSON")
    terminal_pickup: Optional[str] = Field(default=None, description="Terminal Key для Самовывоза")
    terminal_delivery: Optional[str] = Field(default=None, description="Terminal Key для Доставки")
    merchant_id: Optional[str] = Field(default=None, description="Идентификатор мерчанта СБП (Merchant ID)")
    sbp_terminal_id: Optional[str] = Field(default="42734785", description="Terminal ID кассы СБП (TID)")
    sbp_secret_key: Optional[str] = Field(default=None, description="Секретный ключ подписи СБП (HMAC-SHA256)")
    terminal_names: Optional[str] = Field(default=None, description="Пользовательские названия терминалов в JSON: {terminal_key: custom_name}")
    
    # Настройки интернет-эквайринга Т-Банка (Merchant API / e-commerce)
    acquiring_terminal_key: Optional[str] = Field(default=None, description="TerminalKey интернет-эквайринга")
    acquiring_password: Optional[str] = Field(default=None, description="Пароль терминала интернет-эквайринга (Секретный ключ подписи)")
    acquiring_is_active: bool = Field(default=True, description="Флаг активности интернет-эквайринга")
    webhook_secret: Optional[str] = Field(default=None, description="Секретный токен для проверки вебхуков")

    # Флаг активности интеграции
    is_active: bool = Field(default=False, description="Глобальный флаг активации подключения")

    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)

class TBankAccountStatement(SQLModel, table=True):
    """Банковские операции по расчетным счетам компании (кэш выписок для сверки)"""
    __tablename__ = "tbank_statements"

    id: Optional[int] = Field(default=None, primary_key=True)
    account_number: str = Field(description="Номер расчетного счета компании")
    charge_date: datetime = Field(description="Дата списания/поступления средств")
    amount: float = Field(description="Сумма операции в рублях")
    payment_purpose: str = Field(description="Назначение платежа")
    payer_name: Optional[str] = Field(default=None, description="Наименование плательщика")
    payer_inn: Optional[str] = Field(default=None, description="ИНН плательщика")
    payer_account: Optional[str] = Field(default=None, description="Счет плательщика")
    payer_bank_bic: Optional[str] = Field(default=None, description="БИК банка плательщика")
    
    # Ссылка на сопоставленный заказ
    matched_order_id: Optional[int] = Field(default=None, description="ID сопоставленного заказа")
    
    created_at: datetime = Field(default_factory=utc_now)
