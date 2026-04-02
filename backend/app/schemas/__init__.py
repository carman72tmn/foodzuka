"""
Pydantic схемы для валидации данных API
"""
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from app.models.order import OrderStatus


# ============= Схемы компаний, филиалов и зон =============

class CompanyBase(BaseModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    inn: Optional[str] = None
    is_active: bool = True
    iiko_api_login: Optional[str] = None
    iiko_organization_id: Optional[str] = None

class CompanyCreate(CompanyBase):
    pass

class CompanyUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    inn: Optional[str] = None
    is_active: Optional[bool] = None
    iiko_api_login: Optional[str] = None
    iiko_organization_id: Optional[str] = None

class CompanyResponse(CompanyBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class BranchBase(BaseModel):
    name: str = Field(max_length=255)
    address: str = Field(max_length=500)
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: bool = True
    is_accepting_orders: bool = True
    is_accepting_delivery: bool = True
    is_accepting_pickup: bool = True
    min_order_amount: float = 0.0
    free_delivery_threshold: float = 0.0
    working_hours: Optional[str] = None
    company_id: int
    iiko_terminal_id: Optional[str] = None

class BranchCreate(BranchBase):
    pass

class BranchUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    address: Optional[str] = Field(None, max_length=500)
    phone: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_active: Optional[bool] = None
    is_accepting_orders: Optional[bool] = None
    is_accepting_delivery: Optional[bool] = None
    is_accepting_pickup: Optional[bool] = None
    min_order_amount: Optional[float] = None
    free_delivery_threshold: Optional[float] = None
    working_hours: Optional[str] = None
    company_id: Optional[int] = None
    iiko_terminal_id: Optional[str] = None

class BranchResponse(BranchBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DeliveryZoneBase(BaseModel):
    name: str = Field(max_length=255)
    branch_id: int
    polygon_coordinates: str
    min_order_amount: Decimal = Field(default=Decimal("0.0"), ge=0)
    delivery_cost: Decimal = Field(default=Decimal("0.0"), ge=0)
    free_delivery_from: Optional[Decimal] = Field(None, ge=0)
    is_active: bool = True

class DeliveryZoneCreate(DeliveryZoneBase):
    pass

class DeliveryZoneUpdate(BaseModel):
    name: Optional[str] = Field(None, max_length=255)
    branch_id: Optional[int] = None
    polygon_coordinates: Optional[str] = None
    min_order_amount: Optional[Decimal] = Field(None, ge=0)
    delivery_cost: Optional[Decimal] = Field(None, ge=0)
    free_delivery_from: Optional[Decimal] = Field(None, ge=0)
    is_active: Optional[bool] = None

class DeliveryZoneResponse(DeliveryZoneBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


# ============= Схемы категорий =============

class CategoryBase(BaseModel):
    """Базовые поля категории"""
    name: str = Field(max_length=255)
    description: Optional[str] = None
    sort_order: int = 0
    is_active: bool = True


class CategoryCreate(CategoryBase):
    """Создание категории"""
    pass


class CategoryUpdate(BaseModel):
    """Обновление категории"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    sort_order: Optional[int] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    """Ответ API с категорией"""
    id: int
    iiko_id: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Схемы товаров =============

class ProductSizeResponse(BaseModel):
    """Размер товара"""
    id: int
    iiko_id: str
    name: str
    price: Decimal
    is_default: bool

    model_config = ConfigDict(from_attributes=True)


class ProductModifierResponse(BaseModel):
    """Конкретный модификатор"""
    id: int
    iiko_id: str
    name: str
    price: Decimal
    default_amount: int
    min_amount: int
    max_amount: int

    model_config = ConfigDict(from_attributes=True)


class ProductModifierGroupResponse(BaseModel):
    """Группа модификаторов"""
    id: int
    iiko_id: str
    name: str
    min_amount: int
    max_amount: int
    is_required: bool
    modifiers: List[ProductModifierResponse] = []

    model_config = ConfigDict(from_attributes=True)


class ProductBase(BaseModel):
    """Базовые поля товара"""
    name: str = Field(max_length=255)
    description: Optional[str] = None
    price: Decimal = Field(ge=0)
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_available: bool = True
    sort_order: int = 0
    weight_grams: Optional[int] = None
    volume_ml: Optional[int] = None
    calories: Optional[int] = None
    proteins: Optional[float] = None
    fats: Optional[float] = None
    carbohydrates: Optional[float] = None
    is_popular: bool = False
    old_price: Optional[Decimal] = Field(None, ge=0)
    max_discount_percent: Optional[int] = Field(None, ge=0, le=100)
    bonus_accrual_percent: Optional[int] = Field(None, ge=0, le=100)
    stop_list_branch_ids: List[int] = []


class ProductCreate(ProductBase):
    """Создание товара"""
    pass


class ProductUpdate(BaseModel):
    """Обновление товара"""
    name: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    price: Optional[Decimal] = Field(None, ge=0)
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    is_available: Optional[bool] = None
    sort_order: Optional[int] = None
    weight_grams: Optional[int] = None
    volume_ml: Optional[int] = None
    calories: Optional[int] = None
    proteins: Optional[float] = None
    fats: Optional[float] = None
    carbohydrates: Optional[float] = None
    is_popular: Optional[bool] = None
    old_price: Optional[Decimal] = Field(None, ge=0)
    max_discount_percent: Optional[int] = Field(None, ge=0, le=100)
    bonus_accrual_percent: Optional[int] = Field(None, ge=0, le=100)
    stop_list_branch_ids: Optional[List[int]] = None


class ProductResponse(ProductBase):
    """Ответ API с товаром"""
    id: int
    iiko_id: Optional[str] = None
    article: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    sizes: List[ProductSizeResponse] = []
    modifier_groups: List[ProductModifierGroupResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ============= Схемы заказов =============

class OrderItemCreate(BaseModel):
    """Позиция в новом заказе"""
    product_id: int
    quantity: int = Field(ge=1)


class OrderItemResponse(BaseModel):
    """Ответ API с позицией заказа"""
    id: int
    product_id: int
    product_name: str
    quantity: int
    price: Decimal
    total: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderCreate(BaseModel):
    """Создание нового заказа"""
    telegram_user_id: int
    telegram_username: Optional[str] = None
    branch_id: int
    customer_name: str = Field(max_length=255)
    customer_phone: str = Field(max_length=20)
    delivery_address: str = Field(max_length=500)
    comment: Optional[str] = None
    bonus_spent: Optional[Decimal] = Field(default=Decimal("0.00"), ge=0)
    promo_code: Optional[str] = Field(default=None, max_length=100)
    items: List[OrderItemCreate] = Field(min_length=1)


class OrderUpdate(BaseModel):
    """Обновление заказа"""
    status: Optional[OrderStatus] = None
    customer_name: Optional[str] = Field(None, max_length=255)
    customer_phone: Optional[str] = Field(None, max_length=20)
    delivery_address: Optional[str] = Field(None, max_length=500)
    branch_id: Optional[int] = None
    comment: Optional[str] = None


class OrderResponse(BaseModel):
    """Ответ API с заказом"""
    id: int
    telegram_user_id: Optional[int] = None
    telegram_username: Optional[str] = None
    customer_name: Optional[str] = None
    customer_phone: Optional[str] = None
    delivery_address: Optional[str] = None
    total_amount: Decimal
    bonus_spent: Decimal
    total_discount: Decimal
    branch_id: Optional[int] = None
    promo_code_id: Optional[int] = None
    status: OrderStatus
    iiko_order_id: Optional[str] = None
    comment: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    customer_id: Optional[int] = None
    items: List[OrderItemResponse] = []

    model_config = ConfigDict(from_attributes=True)


# ============= Схемы синхронизации с iiko =============

class IikoSyncResponse(BaseModel):
    """Результат синхронизации с iiko"""
    success: bool
    categories_synced: int = 0
    products_synced: int = 0
    products_updated: int = 0
    stopped_count: int = 0
    message: str


class SyncLogResponse(BaseModel):
    """Лог синхронизации"""
    id: int
    sync_type: str
    status: str
    categories_count: int
    products_count: int
    details: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Схемы настроек iiko =============

class IikoSettingsCreate(BaseModel):
    """Создание/обновление настроек iiko"""
    api_login: str = Field(max_length=500)
    organization_id: Optional[str] = None
    external_menu_id: Optional[str] = None
    terminal_group_id: Optional[str] = None
    payment_type_cash: Optional[str] = None
    payment_type_card: Optional[str] = None
    payment_type_online: Optional[str] = None
    payment_type_bonus: Optional[str] = None
    bonus_limit_percent: int = Field(default=0, ge=0, le=100)
    discount_id: Optional[str] = None
    no_pass_promo: bool = False
    no_use_bonus: bool = False
    no_use_iiko_promo: bool = False
    fallback_email: Optional[str] = None
    fallback_telegram_id: Optional[str] = None
    webhook_url: Optional[str] = None
    webhook_auth_token: Optional[str] = None
    resto_url: Optional[str] = None
    resto_login: Optional[str] = None
    resto_password: Optional[str] = None


class IikoSettingsResponse(IikoSettingsCreate):
    """Ответ API с настройками iiko"""
    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def model_validate(cls, obj, **kwargs):
        """Маскируем пароль и ключи при выводе"""
        instance = super().model_validate(obj, **kwargs)
        if instance.resto_password:
            instance.resto_password = "********"
        if instance.api_login and len(instance.api_login) > 8:
            instance.api_login = f"{instance.api_login[:4]}...{instance.api_login[-4:]}"
        return instance


class IikoConnectionTestResponse(BaseModel):
    """Результат проверки подключения к iiko"""
    success: bool
    token_valid: bool = False
    organizations: list = []
    error: Optional[str] = None


class IikoWebhookEventResponse(BaseModel):
    """Событие вебхука"""
    id: int
    event_type: str
    event_id: str
    payload: dict
    processed: bool
    error: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============= Схемы маркетинга и лояльности =============

class PromoCodeBase(BaseModel):
    name: str = Field(max_length=255)
    code: str = Field(max_length=100)
    description: Optional[str] = None
    is_active: bool = True
    promo_type: str = Field(max_length=20)
    discount_value: Decimal = Field(default=0)
    gift_product_ids: Optional[str] = None
    usage_type: str = Field(default="multi", max_length=20)
    max_uses: Optional[int] = None
    no_combine: bool = False
    first_order_only: bool = False
    min_order_amount: Optional[Decimal] = None
    min_items_count: Optional[int] = None
    required_product_ids: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    time_from: Optional[str] = None
    time_until: Optional[str] = None
    valid_days: Optional[str] = None
    platforms: Optional[str] = None
    delivery_types: Optional[str] = None
    branch_ids: Optional[str] = None

class PromoCodeCreate(PromoCodeBase):
    pass

class PromoCodeUpdate(BaseModel):
    name: Optional[str] = None
    code: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    promo_type: Optional[str] = None
    discount_value: Optional[Decimal] = None
    gift_product_ids: Optional[str] = None
    usage_type: Optional[str] = None
    max_uses: Optional[int] = None
    no_combine: Optional[bool] = None
    first_order_only: Optional[bool] = None
    min_order_amount: Optional[Decimal] = None
    min_items_count: Optional[int] = None
    required_product_ids: Optional[str] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    time_from: Optional[str] = None
    time_until: Optional[str] = None
    valid_days: Optional[str] = None
    platforms: Optional[str] = None
    delivery_types: Optional[str] = None
    branch_ids: Optional[str] = None

class PromoCodeResponse(PromoCodeBase):
    id: int
    current_uses: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ActionBase(BaseModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    priority: int = 0
    image_url: Optional[str] = None
    action_type: str = Field(max_length=50, default="gift_product")
    min_order_amount: Optional[Decimal] = None
    gift_product_ids: Optional[str] = None
    discount_value: Decimal = Field(default=0)
    first_order_only: bool = False
    no_combine: bool = False
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    valid_days: Optional[str] = None
    time_from: Optional[str] = None
    time_until: Optional[str] = None

class ActionCreate(ActionBase):
    pass

class ActionUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    priority: Optional[int] = None
    image_url: Optional[str] = None
    action_type: Optional[str] = None
    min_order_amount: Optional[Decimal] = None
    gift_product_ids: Optional[str] = None
    discount_value: Optional[Decimal] = None
    first_order_only: Optional[bool] = None
    no_combine: Optional[bool] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None
    valid_days: Optional[str] = None
    time_from: Optional[str] = None
    time_until: Optional[str] = None

class ActionResponse(ActionBase):
    id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class CustomerBase(BaseModel):
    phone: str = Field(max_length=20)
    telegram_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    birthday: Optional[datetime] = None
    is_blocked: bool = False

class CustomerCreate(CustomerBase):
    pass

class CustomerUpdate(BaseModel):
    phone: Optional[str] = None
    telegram_id: Optional[int] = None
    name: Optional[str] = None
    email: Optional[str] = None
    birthday: Optional[datetime] = None
    is_blocked: Optional[bool] = None

class CustomerResponse(CustomerBase):
    id: int
    loyalty_status_id: Optional[int]
    bonus_points: Decimal
    status_points: int
    iiko_customer_id: Optional[str]
    total_orders_count: int
    total_orders_amount: Decimal
    last_order_date: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class NpsReviewBase(BaseModel):
    order_id: int
    customer_id: Optional[int] = None
    score: int = Field(ge=1, le=5)
    kitchen_score: Optional[int] = Field(None, ge=1, le=5)
    delivery_score: Optional[int] = Field(None, ge=1, le=5)
    comment: Optional[str] = None

class NpsReviewCreate(NpsReviewBase):
    pass

class NpsReviewUpdate(BaseModel):
    is_processed: Optional[bool] = None
    manager_comment: Optional[str] = None

class NpsReviewResponse(NpsReviewBase):
    id: int
    is_processed: bool
    manager_comment: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]
    model_config = ConfigDict(from_attributes=True)

# ============= Схемы рассылок, историй и воронок =============

class MailingBase(BaseModel):
    title: str = Field(max_length=255)
    message_text: str
    image_url: Optional[str] = None
    channel: str = Field(default="telegram", max_length=50)
    audience_filters: Optional[str] = None
    scheduled_at: Optional[datetime] = None

class MailingCreate(MailingBase):
    pass

class MailingUpdate(BaseModel):
    title: Optional[str] = None
    message_text: Optional[str] = None
    image_url: Optional[str] = None
    channel: Optional[str] = None
    audience_filters: Optional[str] = None
    scheduled_at: Optional[datetime] = None
    status: Optional[str] = None

class MailingResponse(MailingBase):
    id: int
    target_count: int
    sent_count: int
    error_count: int
    status: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class StoryBase(BaseModel):
    title: str = Field(max_length=255)
    image_url: str = Field(max_length=500)
    video_url: Optional[str] = Field(None, max_length=500)
    action_type: Optional[str] = Field(None, max_length=50)
    action_target: Optional[str] = Field(None, max_length=255)
    action_button_text: Optional[str] = Field("Подробнее", max_length=50)
    is_active: bool = True
    sort_order: int = 0
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class StoryCreate(StoryBase):
    pass

class StoryUpdate(BaseModel):
    title: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    action_type: Optional[str] = None
    action_target: Optional[str] = None
    action_button_text: Optional[str] = None
    is_active: Optional[bool] = None
    sort_order: Optional[int] = None
    valid_from: Optional[datetime] = None
    valid_until: Optional[datetime] = None

class StoryResponse(StoryBase):
    id: int
    views_count: int
    clicks_count: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)


class FunnelBase(BaseModel):
    name: str = Field(max_length=255)
    description: Optional[str] = None
    is_active: bool = True
    trigger_type: str = Field(default="no_orders_n_days", max_length=50)
    trigger_value: Optional[int] = None
    steps: str = Field(default="[]")

class FunnelCreate(FunnelBase):
    pass

class FunnelUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    is_active: Optional[bool] = None
    trigger_type: Optional[str] = None
    trigger_value: Optional[int] = None
    steps: Optional[str] = None

class FunnelResponse(FunnelBase):
    id: int
    clients_entered: int
    clients_converted: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)
