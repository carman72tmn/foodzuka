"""
API эндпоинты для работы с кухней (техкарты, экран повара, зоны приготовления)
"""
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlmodel import Session, select, and_
from sqlalchemy.orm import selectinload
from app.core.database import get_session
from app.api.deps import require_permission, get_current_user
from app.models.product import Product, KitchenZone, ProductRecipe
from app.models.order import Order, OrderItem, OrderStatus
from app.models.user import User
from app.models.iiko_settings import IikoSettings
from app.services.order_status_history_service import append_order_status_history
from pydantic import BaseModel

router = APIRouter(prefix="/kitchen", tags=["Kitchen"])

# =========================================================================
# Схемы валидации данных (Pydantic)
# =========================================================================

class KitchenZoneCreate(BaseModel):
    name: str
    color: Optional[str] = "#2196F3"
    description: Optional[str] = None

class KitchenZoneResponse(BaseModel):
    id: int
    name: str
    color: str
    description: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class IngredientSchema(BaseModel):
    name: str
    gross: float # брутто, г
    net: float   # нетто, г
    output: float # выход, г
    iiko_id: Optional[str] = None

class RecipeUpdate(BaseModel):
    ingredients: List[IngredientSchema]
    technology: Optional[str] = None
    appearance: Optional[str] = None
    critical_points: Optional[str] = None
    kitchen_zone_id: Optional[int] = None

class RecipeResponse(BaseModel):
    product_id: int
    product_name: str
    article: Optional[str] = None
    image_url: Optional[str] = None
    weight_grams: Optional[int] = None
    calories: Optional[int] = None
    proteins: Optional[float] = None
    fats: Optional[float] = None
    carbohydrates: Optional[float] = None
    kitchen_zone_id: Optional[int] = None
    ingredients: List[IngredientSchema] = []
    technology: Optional[str] = None
    appearance: Optional[str] = None
    critical_points: Optional[str] = None
    updated_at: Optional[datetime] = None

class ProductCompactResponse(BaseModel):
    id: int
    name: str
    article: Optional[str] = None
    image_url: Optional[str] = None
    category_id: Optional[int] = None
    kitchen_zone_id: Optional[int] = None
    has_recipe: bool

class KitchenOrderItemResponse(BaseModel):
    id: int
    product_id: Optional[int]
    product_name: str
    quantity: int
    size_name: Optional[str]
    comment: Optional[str]
    modifiers: Optional[List[Dict[str, Any]]]
    kitchen_status: str
    kitchen_started_at: Optional[datetime]
    kitchen_ready_at: Optional[datetime]
    kitchen_zone_id: Optional[int]
    kitchen_zone_name: Optional[str]
    kitchen_zone_color: Optional[str]
    ingredients: List[IngredientSchema] = []

class KitchenOrderResponse(BaseModel):
    id: int
    external_number: Optional[str]
    status: str
    order_type: Optional[str]
    expected_time: Optional[datetime]
    iiko_creation_time: Optional[datetime]
    comment: Optional[str]
    items: List[KitchenOrderItemResponse]
    created_at: datetime

# =========================================================================
# 1. Зоны приготовления (Kitchen Zones)
# =========================================================================

@router.get("/zones", response_model=List[KitchenZoneResponse])
def get_zones(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_recipes_view"))
):
    """Получить список всех зон приготовления блюд"""
    zones = session.exec(select(KitchenZone).order_by(KitchenZone.name)).all()
    return zones

@router.post("/zones", response_model=KitchenZoneResponse, status_code=status.HTTP_201_CREATED)
def create_zone(
    zone_data: KitchenZoneCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_zones_manage"))
):
    """Создать новую зону приготовления"""
    # Проверка на дубликат имени
    existing = session.exec(select(KitchenZone).where(KitchenZone.name == zone_data.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="Зона с таким названием уже существует")
        
    zone = KitchenZone(**zone_data.model_dump())
    session.add(zone)
    session.commit()
    session.refresh(zone)
    return zone

@router.put("/zones/{zone_id}", response_model=KitchenZoneResponse)
def update_zone(
    zone_id: int,
    zone_data: KitchenZoneCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_zones_manage"))
):
    """Обновить данные зоны приготовления"""
    zone = session.get(KitchenZone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Зона не найдена")
        
    # Проверка на уникальность имени при изменении
    existing = session.exec(select(KitchenZone).where(and_(KitchenZone.name == zone_data.name, KitchenZone.id != zone_id))).first()
    if existing:
        raise HTTPException(status_code=400, detail="Зона с таким названием уже существует")
        
    zone.name = zone_data.name
    zone.color = zone_data.color
    zone.description = zone_data.description
    zone.updated_at = datetime.now(timezone.utc)
    
    session.add(zone)
    session.commit()
    session.refresh(zone)
    return zone

@router.delete("/zones/{zone_id}")
def delete_zone(
    zone_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_zones_manage"))
):
    """Удалить зону приготовления"""
    zone = session.get(KitchenZone, zone_id)
    if not zone:
        raise HTTPException(status_code=404, detail="Зона не найдена")
        
    session.delete(zone)
    session.commit()
    return {"status": "success", "message": "Зона удалена"}

# =========================================================================
# 2. Технологические карты (Recipes)
# =========================================================================

@router.get("/recipes/products", response_model=List[ProductCompactResponse])
def get_recipe_products(
    search: Optional[str] = None,
    category_id: Optional[int] = None,
    kitchen_zone_id: Optional[int] = None,
    has_recipe: Optional[bool] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_recipes_view"))
):
    """Получить список товаров (блюд) для каталога техкарт"""
    query = select(Product).options(selectinload(Product.recipe))
    
    if search:
        search_filter = f"%{search}%"
        query = query.where(
            (Product.name.ilike(search_filter)) | 
            (Product.article.ilike(search_filter))
        )
        
    if category_id is not None:
        query = query.where(Product.category_id == category_id)
        
    if kitchen_zone_id is not None:
        query = query.where(Product.kitchen_zone_id == kitchen_zone_id)
        
    products = session.exec(query).all()
    
    result = []
    for p in products:
        has_rec = p.recipe is not None
        
        # Если включен фильтр по наличию техкарты
        if has_recipe is not None and has_rec != has_recipe:
            continue
            
        result.append({
            "id": p.id,
            "name": p.name,
            "article": p.article,
            "image_url": p.image_url,
            "category_id": p.category_id,
            "kitchen_zone_id": p.kitchen_zone_id,
            "has_recipe": has_rec
        })
        
    return result

@router.get("/recipes/{product_id}", response_model=RecipeResponse)
def get_recipe(
    product_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_recipes_view"))
):
    """Получить техкарту конкретного блюда"""
    product = session.exec(
        select(Product)
        .options(selectinload(Product.recipe))
        .where(Product.id == product_id)
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
        
    recipe = product.recipe
    
    return {
        "product_id": product.id,
        "product_name": product.name,
        "article": product.article,
        "image_url": product.image_url,
        "weight_grams": product.weight_grams,
        "calories": product.calories,
        "proteins": product.proteins,
        "fats": product.fats,
        "carbohydrates": product.carbohydrates,
        "kitchen_zone_id": product.kitchen_zone_id,
        "ingredients": recipe.ingredients if recipe else [],
        "technology": recipe.technology if recipe else "",
        "appearance": recipe.appearance if recipe else "",
        "critical_points": recipe.critical_points if recipe else "",
        "updated_at": recipe.updated_at if recipe else None
    }

@router.put("/recipes/{product_id}", response_model=RecipeResponse)
def update_recipe(
    product_id: int,
    recipe_data: RecipeUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_recipes_edit"))
):
    """Создать или обновить техкарту блюда"""
    product = session.exec(
        select(Product)
        .options(selectinload(Product.recipe))
        .where(Product.id == product_id)
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
        
    # Обновляем зону приготовления у самого товара
    product.kitchen_zone_id = recipe_data.kitchen_zone_id
    session.add(product)
    
    recipe = product.recipe
    if not recipe:
        recipe = ProductRecipe(
            product_id=product_id,
            ingredients=[ing.model_dump() for ing in recipe_data.ingredients],
            technology=recipe_data.technology,
            appearance=recipe_data.appearance,
            critical_points=recipe_data.critical_points,
            updated_at=datetime.now(timezone.utc)
        )
    else:
        recipe.ingredients = [ing.model_dump() for ing in recipe_data.ingredients]
        recipe.technology = recipe_data.technology
        recipe.appearance = recipe_data.appearance
        recipe.critical_points = recipe_data.critical_points
        recipe.updated_at = datetime.now(timezone.utc)
        
    session.add(recipe)
    session.commit()
    session.refresh(product)
    session.refresh(recipe)
    
    return {
        "product_id": product.id,
        "product_name": product.name,
        "article": product.article,
        "image_url": product.image_url,
        "weight_grams": product.weight_grams,
        "calories": product.calories,
        "proteins": product.proteins,
        "fats": product.fats,
        "carbohydrates": product.carbohydrates,
        "kitchen_zone_id": product.kitchen_zone_id,
        "ingredients": recipe.ingredients,
        "technology": recipe.technology,
        "appearance": recipe.appearance,
        "critical_points": recipe.critical_points,
        "updated_at": recipe.updated_at
    }

@router.post("/recipes/import-iiko")
async def import_recipes_from_iiko(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_recipes_edit"))
):
    """
    Принудительно импортировать технологические карты и цеха из iiko Resto (Backoffice)
    """
    from app.services.iiko_sync_service import iiko_sync_service
    res = await iiko_sync_service.sync_kitchen_recipes_and_zones(session)
    if not res.get("success"):
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=res.get("message", "Ошибка при синхронизации с iiko")
        )
    return res

# =========================================================================
# 3. Экран повара (KDS Orders)
# =========================================================================

@router.get("/orders", response_model=List[KitchenOrderResponse])
def get_kitchen_orders(
    zone_ids: Optional[str] = Query(None, description="Список ID цехов через запятую"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_screen_view"))
):
    """
    Получить активные заказы для кухни.
    Показывает заказы со статусом new, unconfirmed, confirmed, preparing, cooking, assembling.
    Если передан zone_ids, на бэкенде фильтруются заказы, в которых есть позиции этих зон,
    и в выводе возвращаются только те позиции, которые относятся к этим зонам.
    """
    active_statuses = [
        OrderStatus.new,
        OrderStatus.unconfirmed,
        OrderStatus.confirmed,
        OrderStatus.preparing,
        OrderStatus.cooking,
        OrderStatus.assembling
    ]
    
    query = select(Order).where(Order.status.in_(active_statuses)).options(
        selectinload(Order.items)
    ).order_by(Order.expected_time.asc(), Order.created_at.asc())
    
    orders = session.exec(query).all()
    
    # Получаем мапу зон для быстрого поиска имен/цветов
    zones = session.exec(select(KitchenZone)).all()
    zone_map = {z.id: z for z in zones}
    
    # Парсим zone_ids в список цехов
    target_zones = None
    if zone_ids:
        try:
            target_zones = [int(z.strip()) for z in zone_ids.split(",") if z.strip().isdigit()]
        except Exception:
            target_zones = None
            
    result = []
    for order in orders:
        items_data = []
        has_items_for_zone = False
        
        for item in order.items:
            k_zone_id = item.kitchen_zone_id
            prod = None
            if item.product_id:
                prod = session.exec(
                    select(Product)
                    .options(selectinload(Product.recipe))
                    .where(Product.id == item.product_id)
                ).first()
                if prod and k_zone_id is None:
                    k_zone_id = prod.kitchen_zone_id
                    
            # Фильтруем по списку зон, если параметр передан
            if target_zones is not None and k_zone_id not in target_zones:
                continue
                
            has_items_for_zone = True
            
            zone_name = "—"
            zone_color = "#9E9E9E"
            if k_zone_id in zone_map:
                zone_name = zone_map[k_zone_id].name
                zone_color = zone_map[k_zone_id].color
                
            items_data.append({
                "id": item.id,
                "product_id": item.product_id,
                "product_name": item.product_name,
                "quantity": item.quantity,
                "size_name": item.size_name,
                "comment": item.comment,
                "modifiers": item.modifiers,
                "kitchen_status": item.kitchen_status or "pending",
                "kitchen_started_at": item.kitchen_started_at,
                "kitchen_ready_at": item.kitchen_ready_at,
                "kitchen_zone_id": k_zone_id,
                "kitchen_zone_name": zone_name,
                "kitchen_zone_color": zone_color,
                "ingredients": prod.recipe.ingredients if (prod and prod.recipe) else []
            })
            
        # Добавляем заказ в выдачу, только если в нем есть позиции для выбранного цеха
        if has_items_for_zone:
            result.append({
                "id": order.id,
                "external_number": order.external_number,
                "status": order.status.value,
                "order_type": order.order_type,
                "expected_time": order.expected_time,
                "iiko_creation_time": order.iiko_creation_time,
                "comment": order.comment,
                "items": items_data,
                "created_at": order.created_at
            })
            
    return result

@router.post("/items/{item_id}/status")
def update_item_status(
    item_id: int,
    status_name: str = Query(..., description="cooking или ready"),
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_screen_edit"))
):
    """Изменить статус приготовления отдельного блюда на кухне"""
    item = session.get(OrderItem, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Позиция заказа не найдена")
        
    order = session.get(Order, item.order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    status_name = status_name.lower()
    if status_name not in ("cooking", "ready", "pending"):
        raise HTTPException(status_code=400, detail="Неверный статус. Допустимо: pending, cooking, ready")
        
    item.kitchen_status = status_name
    
    if status_name == "cooking":
        item.kitchen_started_at = datetime.now(timezone.utc)
        # Если весь заказ еще не готовится, переводим его в статус cooking
        if order.status in (OrderStatus.new, OrderStatus.unconfirmed, OrderStatus.confirmed, OrderStatus.preparing):
            order.status = OrderStatus.cooking
            order.updated_at = datetime.now(timezone.utc)
            session.add(order)
            
    elif status_name == "ready":
        item.kitchen_ready_at = datetime.now(timezone.utc)
        
    session.add(item)
    session.commit()
    session.refresh(item)
    
    # Проверяем готовность остальных блюд в заказе
    session.refresh(order)
    all_items_query = select(OrderItem).where(OrderItem.order_id == order.id)
    all_items = session.exec(all_items_query).all()
    
    all_ready = all(i.kitchen_status == "ready" for i in all_items)
    
    if all_ready and all_items:
        # Автоматически переводим заказ в статус готовности
        if order.order_type == "Самовывоз":
            order.status = OrderStatus.ready_for_pickup
        else:
            order.status = OrderStatus.ready
            
        order.updated_at = datetime.now(timezone.utc)
        session.add(order)
        session.commit()
        print(f"[Kitchen] Order {order.id} is fully READY. Status updated to {order.status.value}.")
        
    return {
        "status": "success",
        "item_id": item.id,
        "kitchen_status": item.kitchen_status,
        "order_status": order.status.value
    }


@router.post("/orders/{order_id}/start-cooking")
def start_order_cooking(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_screen_edit"))
):
    """Начать приготовление всего заказа (переводит заказ и все блюда в статус cooking)"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    order.status = OrderStatus.cooking
    order.updated_at = datetime.now(timezone.utc)
    append_order_status_history(
        order=order,
        new_status=OrderStatus.cooking,
        session=session,
        comment="Начато приготовление на кухне",
        user=f"Кухня: {current_user.full_name or current_user.username}"
    )
    session.add(order)
    
    # Все позиции переводим в статус cooking
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    for item in items:
        if item.kitchen_status != "ready":
            item.kitchen_status = "cooking"
            item.kitchen_started_at = datetime.now(timezone.utc)
            session.add(item)
            
    session.commit()
    return {"status": "success", "order_status": order.status.value}


@router.post("/orders/{order_id}/assembling")
def start_order_assembling(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_screen_edit"))
):
    """Перевести заказ в статус 'На сборке'"""
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    order.status = OrderStatus.assembling
    order.updated_at = datetime.now(timezone.utc)
    append_order_status_history(
        order=order,
        new_status=OrderStatus.assembling,
        session=session,
        comment="Заказ передан на сборку",
        user=f"Кухня: {current_user.full_name or current_user.username}"
    )
    session.add(order)
    session.commit()
    return {"status": "success", "order_status": order.status.value}


@router.post("/orders/{order_id}/ready")
async def make_order_ready(
    order_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_screen_edit"))
):
    """
    Отметить заказ как 'Собран/Готов полностью'.
    Переводит все блюда в ready, меняет статус заказа на ready/ready_for_pickup
    и отправляет статус 'Waiting' в iiko Cloud.
    """
    order = session.get(Order, order_id)
    if not order:
        raise HTTPException(status_code=404, detail="Заказ не найден")
        
    # Определяем статус готовности
    new_status = OrderStatus.ready_for_pickup if order.order_type == "Самовывоз" else OrderStatus.ready
    
    order.status = new_status
    order.updated_at = datetime.now(timezone.utc)
    append_order_status_history(
        order=order,
        new_status=new_status,
        session=session,
        comment="Заказ приготовлен и собран",
        user=f"Кухня: {current_user.full_name or current_user.username}"
    )
    session.add(order)
    
    # Все позиции переводим в статус ready
    items = session.exec(select(OrderItem).where(OrderItem.order_id == order.id)).all()
    for item in items:
        if item.kitchen_status != "ready":
            item.kitchen_status = "ready"
            item.kitchen_ready_at = datetime.now(timezone.utc)
            session.add(item)
            
    session.commit()
    
    # Отправляем в iiko Cloud
    settings = session.exec(select(IikoSettings)).first()
    if settings and order.iiko_order_id:
        try:
            from app.services.iiko_service import iiko_service
            await iiko_service.change_delivery_status(
                organization_id=settings.organization_id,
                order_id=order.iiko_order_id,
                delivery_status="Waiting"
            )
            print(f"[Kitchen] Sent 'Waiting' status to iiko for order {order.iiko_order_id}")
        except Exception as e:
            print(f"[Kitchen] Failed to send status to iiko: {e}")
            
    return {"status": "success", "order_status": order.status.value}


@router.get("/recipes/by-iiko-id/{iiko_id}")
def get_recipe_by_iiko_id(
    iiko_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("kitchen_screen_view"))
):
    """Получить техкарту товара/заготовки по его iiko ID"""
    product = session.exec(
        select(Product)
        .options(selectinload(Product.recipe))
        .where(Product.iiko_id == iiko_id)
    ).first()
    
    if not product:
        raise HTTPException(status_code=404, detail="Товар не найден")
        
    recipe = product.recipe
    
    return {
        "product_id": product.id,
        "product_name": product.name,
        "article": product.article,
        "image_url": product.image_url,
        "weight_grams": product.weight_grams,
        "calories": product.calories,
        "proteins": product.proteins,
        "fats": product.fats,
        "carbohydrates": product.carbohydrates,
        "kitchen_zone_id": product.kitchen_zone_id,
        "ingredients": recipe.ingredients if recipe else [],
        "technology": recipe.technology if recipe else "",
        "appearance": recipe.appearance if recipe else "",
        "critical_points": recipe.critical_points if recipe else "",
        "updated_at": recipe.updated_at if recipe else None
    }

