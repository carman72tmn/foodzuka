"""
Модели базы данных для FoodTech
Все модели наследуются от SQLModel для использования с FastAPI
"""
from .user import User
from .role import Role, Permission, RolePermissionLink

from .category import Category
from .product import Product, ProductSize, ProductModifierGroup, ProductModifier
from .order import Order, OrderItem, OrderStatus
from .iiko_settings import IikoSettings
from .sync_log import SyncLog, SyncStatus
from .system_log import SystemLog
from .audit_log import AuditLog
from .loyalty import LoyaltyStatus, LoyaltyRule, LoyaltyTransaction
from .iiko_loyalty import IikoLoyaltyItem
from .promo_code import PromoCode
from .iiko_webhook_event import IikoWebhookEvent
from .company import Company, Branch, DeliveryZone, CustomPolygon
from .customer import Customer
from .action import Action
from .nps import NpsReview
from .mailing import Mailing
from .chat import ChatMessage, ChatReadState
from .story import Story
from .funnel import Funnel
from .olap_revenue import OlapRevenueRecord
from .employee import Employee, Shift, CourierOrder
from .vk_user import VkUser
from .vk_activity import VkActivity
from .vk_settings import VkSettings
from .vk_webhook_log import VkWebhookLog
from .vk_message import VkMessage
from .bot_settings import BotSettings
from .payment_type import PaymentType
from .yandex_settings import YandexSettings
from .max_settings import MaxSettings, MaxBot
from .vk_bot import (
    VkBotAccount, 
    VkBotGroup, 
    VkBotAccountGroupLink, 
    VkBotSubscription, 
    VkBotMessageLog,
    DeliveryMode,
    MessageStatus
)
from .scheduled_task import ScheduledTask
from .mailing_cascade import MailingCascade, MailingCascadeStep

__all__ = [
    "User",
    "Role",
    "Permission",
    "RolePermissionLink",

    "Category",
    "Product",
    "ProductSize",
    "ProductModifierGroup",
    "ProductModifier",
    "Order",
    "OrderItem",
    "OrderStatus",
    "IikoSettings",
    "SyncLog",
    "SyncStatus",
    "ChatMessage",
    "ChatReadState",
    "SystemLog",
    "AuditLog",
    "LoyaltyStatus",
    "LoyaltyRule",
    "LoyaltyTransaction",
    "IikoLoyaltyItem",
    "PromoCode",
    "IikoWebhookEvent",
    "Company",
    "Branch",
    "DeliveryZone",
    "CustomPolygon",
    "Customer",
    "Action",
    "NpsReview",
    "Mailing",
    "Story",
    "Funnel",
    "OlapRevenueRecord",
    "Employee",
    "Shift",
    "CourierOrder",
    "VkUser",
    "VkActivity",
    "VkSettings",
    "VkWebhookLog",
    "BotSettings",
    "PaymentType",
    "YandexSettings",
    "VkBotAccount",
    "VkBotGroup",
    "VkBotAccountGroupLink",
    "VkBotSubscription",
    "VkBotMessageLog",
    "DeliveryMode",
    "MessageStatus",
    "ScheduledTask",
    "VkMessage",
    "MaxSettings",
    "MaxBot",
    "MailingCascade",
    "MailingCascadeStep",
]

# Форсируем инициализацию всех мапперов SQLAlchemy
from sqlalchemy.orm import configure_mappers
try:
    configure_mappers()
except Exception:
    pass

