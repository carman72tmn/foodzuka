from typing import Optional
from datetime import datetime, timezone
from sqlmodel import Field, SQLModel

class AdminNotificationSettings(SQLModel, table=True):
    """Таблица настроек уведомлений для пользователей/админов панели"""
    __tablename__ = "admin_notification_settings"

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: Optional[int] = Field(default=None, foreign_key="users.id", unique=True, index=True)
    
    # Новый заказ
    new_order_sound_enabled: bool = Field(default=True)
    new_order_sound_file: str = Field(default="bell.mp3", max_length=255)
    new_order_push_enabled: bool = Field(default=True)
    new_order_repeat_enabled: bool = Field(default=False)
    new_order_repeat_interval: int = Field(default=30)  # в секундах
    
    # Новая оплата
    new_payment_sound_enabled: bool = Field(default=True)
    new_payment_sound_file: str = Field(default="cash.mp3", max_length=255)
    new_payment_push_enabled: bool = Field(default=True)
    
    # Назначение доставки курьеру
    courier_delivery_sound_enabled: bool = Field(default=True)
    courier_delivery_sound_file: str = Field(default="chime.mp3", max_length=255)
    courier_delivery_push_enabled: bool = Field(default=True)

    # Сообщения чата
    chat_message_sound_enabled: bool = Field(default=True)
    chat_message_sound_file: str = Field(default="sonar.mp3", max_length=255)
    chat_message_push_enabled: bool = Field(default=True)

    # Отмена заказа
    order_cancelled_sound_enabled: bool = Field(default=True)
    order_cancelled_sound_file: str = Field(default="bell.mp3", max_length=255)
    order_cancelled_push_enabled: bool = Field(default=True)

    # Изменение заказа (товары, сумма, адрес)
    order_changed_sound_enabled: bool = Field(default=False)
    order_changed_sound_file: str = Field(default="bell.mp3", max_length=255)
    order_changed_push_enabled: bool = Field(default=False)
    
    # Новая доставка без назначенного курьера
    delivery_unassigned_sound_enabled: bool = Field(default=True)
    delivery_unassigned_sound_file: str = Field(default="chime.mp3", max_length=255)
    delivery_unassigned_push_enabled: bool = Field(default=True)
    
    # Назначена доставка (для конкретного курьера)
    delivery_assigned_sound_enabled: bool = Field(default=True)
    delivery_assigned_sound_file: str = Field(default="chime.mp3", max_length=255)
    delivery_assigned_push_enabled: bool = Field(default=True)
    
    # Изменение времени готовности
    change_cooking_time_sound_enabled: bool = Field(default=True)
    change_cooking_time_sound_file: str = Field(default="click.mp3", max_length=255)
    change_cooking_time_push_enabled: bool = Field(default=True)
    
    # Изменение состава
    change_items_sound_enabled: bool = Field(default=True)
    change_items_sound_file: str = Field(default="click.mp3", max_length=255)
    change_items_push_enabled: bool = Field(default=True)
    
    # Изменение суммы оплаты
    change_amount_sound_enabled: bool = Field(default=True)
    change_amount_sound_file: str = Field(default="click.mp3", max_length=255)
    change_amount_push_enabled: bool = Field(default=True)
    
    # Изменение способа оплаты
    change_payment_sound_enabled: bool = Field(default=True)
    change_payment_sound_file: str = Field(default="click.mp3", max_length=255)
    change_payment_push_enabled: bool = Field(default=True)
    
    # Изменение адреса
    change_address_sound_enabled: bool = Field(default=True)
    change_address_sound_file: str = Field(default="click.mp3", max_length=255)
    change_address_push_enabled: bool = Field(default=True)
    
    order_changed_scope: str = Field(default="all", max_length=50)

    # ==========================================
    # ПЕРСОНАЛЬНЫЕ НАСТРОЙКИ УВЕДОМЛЕНИЙ КУРЬЕРА
    # ==========================================
    # 1. Назначен заказ на доставку
    courier_order_assigned_sound_enabled: bool = Field(default=True)
    courier_order_assigned_sound_file: str = Field(default="chime.mp3", max_length=255)
    courier_order_assigned_push_enabled: bool = Field(default=True)

    # 2. Установление времени приготовления заказа
    courier_cooking_time_set_sound_enabled: bool = Field(default=True)
    courier_cooking_time_set_sound_file: str = Field(default="bell.mp3", max_length=255)
    courier_cooking_time_set_push_enabled: bool = Field(default=True)

    # 3. Изменение времени приготовления заказа
    courier_cooking_time_changed_sound_enabled: bool = Field(default=True)
    courier_cooking_time_changed_sound_file: str = Field(default="click.mp3", max_length=255)
    courier_cooking_time_changed_push_enabled: bool = Field(default=True)

    # 4. Изменение статуса заказа (только готов или отменен)
    courier_status_changed_sound_enabled: bool = Field(default=True)
    courier_status_changed_sound_file: str = Field(default="bell.mp3", max_length=255)
    courier_status_changed_push_enabled: bool = Field(default=True)

    # 5. Изменение суммы заказа
    courier_amount_changed_sound_enabled: bool = Field(default=True)
    courier_amount_changed_sound_file: str = Field(default="cash.mp3", max_length=255)
    courier_amount_changed_push_enabled: bool = Field(default=True)

    # 6. Изменение адреса доставки
    courier_address_changed_sound_enabled: bool = Field(default=True)
    courier_address_changed_sound_file: str = Field(default="doorbell.mp3", max_length=255)
    courier_address_changed_push_enabled: bool = Field(default=True)

    # 7. Изменение способа доставки заказа (изменили на самовывоз)
    courier_changed_to_pickup_sound_enabled: bool = Field(default=True)
    courier_changed_to_pickup_sound_file: str = Field(default="branch.mp3", max_length=255)
    courier_changed_to_pickup_push_enabled: bool = Field(default=True)

    # 8. Заказ убран из доставки
    courier_removed_from_delivery_sound_enabled: bool = Field(default=True)
    courier_removed_from_delivery_sound_file: str = Field(default="error.mp3", max_length=255)
    courier_removed_from_delivery_push_enabled: bool = Field(default=True)

    # 9. Заказ убран из списка доставок выбранного курьера
    courier_unassigned_sound_enabled: bool = Field(default=True)
    courier_unassigned_sound_file: str = Field(default="sonar.mp3", max_length=255)
    courier_unassigned_push_enabled: bool = Field(default=True)

    # 10. Изменение времени доставки заказа
    courier_delivery_time_changed_sound_enabled: bool = Field(default=True)
    courier_delivery_time_changed_sound_file: str = Field(default="water.mp3", max_length=255)
    courier_delivery_time_changed_push_enabled: bool = Field(default=True)

    # 11. Доставка заказа (заказ доставлен курьером) - строго для доставок, отображается в общих уведомлениях
    order_delivered_sound_enabled: bool = Field(default=True)
    order_delivered_sound_file: str = Field(default="chime.mp3", max_length=255)
    order_delivered_push_enabled: bool = Field(default=True)

    # Глобальные переключатели браузерных уведомлений
    disable_browser_notifications_couriers: bool = Field(default=False)
    disable_browser_notifications_all: bool = Field(default=False)
    
    vapid_public_key: Optional[str] = Field(default=None)
    vapid_private_key: Optional[str] = Field(default=None)
    
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
