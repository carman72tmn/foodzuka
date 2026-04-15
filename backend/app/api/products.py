"""
API эндпоинты для работы с товарами
"""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.core.database import get_session
from app.models.product import Product, ProductModifierGroup
from app.schemas import ProductCreate, ProductUpdate, ProductResponse

router = APIRouter(prefix="/products", tags=["Products"])


@router.get("/", response_model=List[ProductResponse])
async def get_products(
    skip: int = 0,
    limit: int = 100,
    category_id: Optional[int] = None,
    is_available: Optional[bool] = None,
    session: Session = Depends(get_session)
):
    """
    Получить список всех товаров

    - **skip**: Количество пропускаемых записей
    - **limit**: Максимальное количество возвращаемых записей
    - **category_id**: Фильтр по категории
    - **is_available**: Фильтр по доступности
    """
    query = select(Product).options(
        selectinload(Product.sizes),
        selectinload(Product.modifier_groups).selectinload(ProductModifierGroup.modifiers)
    ).order_by(Product.sort_order, Product.name).offset(skip).limit(limit)

    if category_id is not None:
        query = query.where(Product.category_id == category_id)

    if is_available is not None:
        query = query.where(Product.is_available == is_available)

    products = session.exec(query).all()
    return products


@router.post("/sync-stop-list")
async def sync_stop_list_products(session: Session = Depends(get_session)):
    """Синхронизировать стоп-лист из iiko"""
    from app.services.iiko_sync_service import iiko_sync_service
    result = await iiko_sync_service.sync_stop_lists(session)
    return result


@router.get("/modifiers/all")
async def get_all_modifiers(session: Session = Depends(get_session)):
    """Получить все группы модификаторов со вложенными модификаторами"""
    from app.models.product import ProductModifierGroup
    from sqlalchemy.orm import selectinload
    groups = session.exec(
        select(ProductModifierGroup).options(
            selectinload(ProductModifierGroup.modifiers)
        )
    ).all()
    result = []
    for g in groups:
        # Найти имя товара
        product = session.get(Product, g.product_id)
        result.append({
            "id": g.id,
            "iiko_id": g.iiko_id,
            "name": g.name,
            "product_id": g.product_id,
            "product_name": product.name if product else "—",
            "min_amount": g.min_amount,
            "max_amount": g.max_amount,
            "is_required": g.is_required,
            "modifiers": [
                {
                    "id": m.id,
                    "iiko_id": m.iiko_id,
                    "name": m.name,
                    "price": float(m.price),
                    "min_amount": m.min_amount,
                    "max_amount": m.max_amount,
                    "default_amount": m.default_amount,
                }
                for m in g.modifiers
            ]
        })
    return result


@router.get("/{product_id}", response_model=ProductResponse)
async def get_product(product_id: int, session: Session = Depends(get_session)):
    """Получить товар по ID"""
    query = select(Product).options(
        selectinload(Product.sizes),
        selectinload(Product.modifier_groups).selectinload(ProductModifierGroup.modifiers)
    ).where(Product.id == product_id)
    product = session.exec(query).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )
    return product


@router.get("/{product_id}/iiko-details")
async def get_product_iiko_details(product_id: int, session: Session = Depends(get_session)):
    """Получить расширенные данные товара напрямую из iiko External Menu"""
    from app.services.iiko_service import iiko_service
    from app.models.iiko_settings import IikoSettings
    product = session.get(Product, product_id)
    if not product or not product.iiko_id:
        raise HTTPException(status_code=404, detail="Товар не найден или не синхронизирован с iiko")

    settings = session.exec(select(IikoSettings)).first()
    if not settings or not settings.external_menu_id:
        raise HTTPException(status_code=400, detail="iiko не настроен или не задан External Menu ID")

    ext_menu = await iiko_service.get_external_menu_by_id(
        settings.external_menu_id,
        api_login=settings.api_login,
        organization_id=settings.organization_id
    )
    for cat in ext_menu.get("itemCategories", []):
        for item in cat.get("items", []):
            if item.get("itemId") == product.iiko_id:
                return item

    raise HTTPException(status_code=404, detail="Товар не найден в iiko меню")


@router.post("/", response_model=ProductResponse, status_code=status.HTTP_201_CREATED)
async def create_product(
    product_data: ProductCreate,
    session: Session = Depends(get_session)
):
    """Создать новую категорию"""
    product = Product(**product_data.model_dump())
    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.patch("/{product_id}", response_model=ProductResponse)
async def update_product(
    product_id: int,
    product_data: ProductUpdate,
    session: Session = Depends(get_session)
):
    """Обновить существующий товар"""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    # Обновляем только предоставленные поля
    update_data = product_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(product, key, value)

    session.add(product)
    session.commit()
    session.refresh(product)
    return product


@router.delete("/{product_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_product(product_id: int, session: Session = Depends(get_session)):
    """Удалить товар"""
    product = session.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with id {product_id} not found"
        )

    session.delete(product)
    session.commit()


@router.delete("/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_products(session: Session = Depends(get_session)):
    """Безвозвратно удаляет все товары (Полезно для чистой синхронизации)"""
    from sqlmodel import delete as sql_delete
    session.exec(sql_delete(Product))
    session.commit()


@router.delete("/modifiers/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_modifiers(session: Session = Depends(get_session)):
    """Удаляет все размеры и группы модификаторов"""
    from sqlmodel import delete as sql_delete
    from app.models.product import ProductSize, ProductModifierGroup, ProductModifier
    session.exec(sql_delete(ProductSize))
    session.exec(sql_delete(ProductModifierGroup))
    session.exec(sql_delete(ProductModifier))
    session.commit()
