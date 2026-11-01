"""

Модели для управления VK Ботом (уведомления сотрудников)

"""

from typing import Optional, List

from datetime import datetime

import enum

from sqlmodel import Field, SQLModel, Relationship

from app.core.datetime_utils import utc_now



class DeliveryMode(str, enum.Enum):

    REALTIME = "realtime"

    INTERVAL = "interval"



class MessageStatus(str, enum.Enum):

    PENDING = "pending"       # В очереди на отправку (дайджест)

    SENT = "sent"             # Отправлено в VK

    DELIVERED = "delivered"   # Доставлено пользователю

    READ = "read"             # Прочитано пользователем

    FAILED = "failed"         # Ошибка отправки



class VkBotAccountGroupLink(SQLModel, table=True):

    """Связь аккаунтов и групп (Many-to-Many)"""

    __tablename__ = "vk_bot_account_group_links"

    

    account_id: Optional[int] = Field(

        default=None, foreign_key="vk_bot_accounts.id", primary_key=True

    )

    group_id: Optional[int] = Field(

        default=None, foreign_key="vk_bot_groups.id", primary_key=True

    )



class VkBotGroup(SQLModel, table=True):

    """Группы аккаунтов (напр. Курьеры, Менеджеры)"""

    __tablename__ = "vk_bot_groups"

    

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(max_length=100, unique=True, description="Название группы")

    

    # Связи

    accounts: List["VkBotAccount"] = Relationship(

        back_populates="groups", link_model=VkBotAccountGroupLink

    )



class VkBotAccount(SQLModel, table=True):

    """Аккаунты получателей уведомлений"""

    __tablename__ = "vk_bot_accounts"

    

    id: Optional[int] = Field(default=None, primary_key=True)

    vk_user_id: Optional[int] = Field(default=None, unique=False, index=True, nullable=True, description="Цифровой ID VK")

    name: str = Field(max_length=255, description="Имя/Должность получателя")

    phone: Optional[str] = Field(default=None, max_length=20, description="Телефон для связи с клиентами")

    is_active: bool = Field(default=True, description="Активен ли аккаунт")

    is_verified: bool = Field(default=False, description="Прошел ли проверку связи")
    employee_id: Optional[int] = Field(default=None, description="ID сотрудника (для связи с ролями/должностями)")
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", nullable=True, index=True, description="ID пользователя системы (админки)")
    tg_user_id: Optional[int] = Field(default=None, description="ID пользователя Telegram")
    max_user_id: Optional[str] = Field(default=None, description="ID пользователя MAX Messenger")
    use_vk: bool = Field(default=True, description="Использовать VK для рассылок")
    use_tg: bool = Field(default=False, description="Использовать Telegram для рассылок")
    use_max: bool = Field(default=False, description="Использовать MAX для рассылок")
    use_sms: bool = Field(default=False, description="Использовать SMS для рассылок")
    is_tg_verified: bool = Field(default=False, description="Telegram связь подтверждена")
    is_max_verified: bool = Field(default=False, description="MAX связь подтверждена")
    send_payment_qr: bool = Field(default=False, description="Отправлять QR на оплату в системной рассылке")
    payment_qr_mode: str = Field(default="all", description="Режим отправки QR на оплату (all / assigned_only)")
    is_courier: bool = Field(default=False, description="Является курьером (проверен в iiko)")

    

    # Связи

    groups: List[VkBotGroup] = Relationship(

        back_populates="accounts", link_model=VkBotAccountGroupLink

    )

    subscriptions: List["VkBotSubscription"] = Relationship(back_populates="account")

    logs: List["VkBotMessageLog"] = Relationship(back_populates="account")



    created_at: datetime = Field(default_factory=utc_now)

    updated_at: datetime = Field(default_factory=utc_now)



class VkTemplate(SQLModel, table=True):

    """Шаблоны сообщений для рассылок"""

    __tablename__ = "vk_templates"

    

    id: Optional[int] = Field(default=None, primary_key=True)

    name: str = Field(max_length=255, description="Название шаблона")

    text: str = Field(description="Текст шаблона с переменными")

    keyboard_json: Optional[str] = Field(default=None, description="JSON клавиатуры VK")
    event_type: Optional[str] = Field(default=None, max_length=100, nullable=True, index=True)
    keyboard_telegram: Optional[str] = Field(default=None, nullable=True, description="JSON клавиатуры Telegram")
    keyboard_max: Optional[str] = Field(default=None, nullable=True, description="JSON клавиатуры MAX")
    target_mode: str = Field(default="all", max_length=50, description="Режим адресации: all / assigned_only / assigned_and_admins")
    is_active: bool = Field(default=True, description="Включено ли уведомление (активность цепочки)")
    include_statuses: Optional[str] = Field(default=None, nullable=True, description="JSON список разрешенных статусов для отправки (order_status_update)")
    attach_sbp_qr: bool = Field(default=False, description="Прикреплять QR-код СБП с надписью суммы, номера и адреса")
    chain_config: Optional[str] = Field(default=None, nullable=True, description="JSON конфигурация логической цепочки проверок")
    description: Optional[str] = Field(default=None, max_length=500, nullable=True, description="Описание сценария/цепочки уведомления")
    vk_bot_id: Optional[int] = Field(default=None, foreign_key="vk_bot_connections.id", nullable=True, index=True, description="ID бота ВКонтакте для отправки (если не задан — основной)")
    send_vk: bool = Field(default=True, description="Отправлять в канал VK")
    send_tg: bool = Field(default=False, description="Отправлять в канал Telegram")
    send_max: bool = Field(default=False, description="Отправлять в канал MAX Messenger")
    send_sms: bool = Field(default=False, description="Отправлять в канал SMS")

    

    created_at: datetime = Field(default_factory=utc_now)

    updated_at: datetime = Field(default_factory=utc_now)



class VkMailing(SQLModel, table=True):

    """Кампании рассылок"""

    __tablename__ = "vk_mailings"

    

    id: Optional[int] = Field(default=None, primary_key=True)

    template_id: int = Field(foreign_key="vk_templates.id")

    title: str = Field(max_length=255, description="Заголовок рассылки")

    audience_filters: Optional[str] = Field(default=None, description="JSON фильтров аудитории")

    

    status: str = Field(default="draft", max_length=20, index=True)

    target_count: int = Field(default=0)

    sent_count: int = Field(default=0)

    error_count: int = Field(default=0)

    

    scheduled_at: Optional[datetime] = Field(default=None)

    created_at: datetime = Field(default_factory=utc_now)

    updated_at: datetime = Field(default_factory=utc_now)



class VkBotSubscription(SQLModel, table=True):

    """Подписки аккаунтов на события"""



    __tablename__ = "vk_bot_subscriptions"

    

    id: Optional[int] = Field(default=None, primary_key=True)

    account_id: int = Field(foreign_key="vk_bot_accounts.id")

    event_type: str = Field(max_length=100, description="Тип события (new_order, shift_close, etc.)")

    delivery_mode: DeliveryMode = Field(default=DeliveryMode.REALTIME, description="Режим доставки")

    interval_minutes: int = Field(default=0, description="Интервал в минутах для дайджестов")

    last_digest_at: Optional[datetime] = Field(default=None, description="Время последней отправки дайджеста")

    

    active_start_hour: int = Field(default=0, ge=0, le=23, description="Час начала активности (0-23)")

    active_end_hour: int = Field(default=23, ge=0, le=23, description="Час окончания активности (0-23)")

    
    send_vk: bool = Field(default=True, description="Отправлять это событие в VK")
    send_tg: bool = Field(default=False, description="Отправлять это событие в Telegram")
    send_max: bool = Field(default=False, description="Отправлять это событие в MAX")
    send_sms: bool = Field(default=False, description="Отправлять это событие в SMS")


    # Связи

    account: VkBotAccount = Relationship(back_populates="subscriptions")



class VkBotMessageLog(SQLModel, table=True):

    """Логи сообщений и статистика"""

    __tablename__ = "vk_bot_message_logs"

    

    id: Optional[int] = Field(default=None, primary_key=True)

    account_id: int = Field(foreign_key="vk_bot_accounts.id")

    vk_message_id: Optional[int] = Field(default=None, description="ID сообщения в VK")

    event_type: Optional[str] = Field(default=None, max_length=100)

    text: str = Field(description="Текст сообщения")

    

    status: MessageStatus = Field(default=MessageStatus.PENDING)

    error_text: Optional[str] = Field(default=None, description="Текст ошибки при отправке")

    

    created_at: datetime = Field(default_factory=utc_now)

    sent_at: Optional[datetime] = Field(default=None, description="Время фактической отправки")

    

    # Связи

    account: VkBotAccount = Relationship(back_populates="logs")


class OrderPaymentQrShare(SQLModel, table=True):
    """Связь отправленных в соцсети QR-кодов для последующего удаления после оплаты"""
    __tablename__ = "order_payment_qr_shares"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(index=True, foreign_key="orders.id")
    channel: str = Field(max_length=50, description="Канал рассылки: vk, tg, max")
    chat_id: str = Field(max_length=100, description="ID чата / пользователя")
    message_id: str = Field(max_length=100, description="ID отправленного сообщения")
    created_at: datetime = Field(default_factory=utc_now)


class CourierOrderNotification(SQLModel, table=True):
    """Детальный лог уведомлений курьерам по заказам со статусами обратной связи"""
    __tablename__ = "courier_order_notifications"

    id: Optional[int] = Field(default=None, primary_key=True)
    order_id: int = Field(index=True, foreign_key="orders.id")
    account_id: Optional[int] = Field(default=None, index=True, foreign_key="vk_bot_accounts.id")
    courier_name: Optional[str] = Field(default=None, max_length=255)
    channel: str = Field(max_length=50, description="vk, tg, max, sms")
    external_message_id: Optional[str] = Field(default=None, max_length=100)
    external_chat_id: Optional[str] = Field(default=None, max_length=100)
    status: str = Field(default="unread", max_length=50, description="failed, unread, read, accepted")
    reaction: Optional[str] = Field(default=None, max_length=100)
    reply_text: Optional[str] = Field(default=None)
    error_text: Optional[str] = Field(default=None)
    sent_at: Optional[datetime] = Field(default=None)
    read_at: Optional[datetime] = Field(default=None)
    accepted_at: Optional[datetime] = Field(default=None)
    created_at: datetime = Field(default_factory=utc_now)
    updated_at: datetime = Field(default_factory=utc_now)



