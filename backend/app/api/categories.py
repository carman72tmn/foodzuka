"""
API эндпоинты для работы с категориями
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.category import Category
from app.schemas import CategoryCreate, CategoryUpdate, CategoryResponse

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=List[CategoryResponse])
async def get_categories(
    skip: int = 0,
    limit: int = 100,
    is_active: bool = None,
    session: Session = Depends(get_session)
):
    """
    Получить список всех категорий

    - **skip**: Количество пропускаемых записей
    - **limit**: Максимальное количество возвращаемых записей
    - **is_active**: Фильтр по активности (опционально)
    """
    query = select(Category).order_by(Category.sort_order, Category.name).offset(skip).limit(limit)

    if is_active is not None:
        query = query.where(Category.is_active == is_active)

    categories = session.exec(query).all()
    return categories


@router.get("/tree", response_model=List[CategoryResponse])
async def get_categories_tree(session: Session = Depends(get_session)):
    """Получить все категории с данными для дерева"""
    query = select(Category).order_by(Category.sort_order, Category.name)
    categories = session.exec(query).all()
    return categories


@router.post("/sync-from-iiko")
async def sync_categories_from_iiko(session: Session = Depends(get_session)):
    """Синхронизировать только категории из iiko External Menu"""
    from app.services.iiko_sync_service import iiko_sync_service
    result = await iiko_sync_service.sync_categories_only(session)
    return result


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: int, session: Session = Depends(get_session)):
    """Получить категорию по ID"""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )
    return category


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    category_data: CategoryCreate,
    session: Session = Depends(get_session)
):
    """Создать новую категорию"""
    category = Category(**category_data.model_dump())
    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.patch("/{category_id}", response_model=CategoryResponse)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    session: Session = Depends(get_session)
):
    """Обновить существующую категорию"""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    # Обновляем только предоставленные поля
    update_data = category_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)

    session.add(category)
    session.commit()
    session.refresh(category)
    return category


@router.delete("/all", status_code=status.HTTP_204_NO_CONTENT)
async def delete_all_categories(session: Session = Depends(get_session)):
    """
    Удалить абсолютно все категории.
    Сначала обнуляет ссылки на категории в товарах, чтобы не нарушить целостность.
    """
    from sqlalchemy import text
    
    # 1. Обнуляем ссылки в товарах
    session.exec(text("UPDATE products SET category_id = NULL"))
    
    # 2. Обнуляем parent_id в самих категориях (чтобы избежать проблем с иерархией при удалении)
    session.exec(text("UPDATE categories SET parent_id = NULL"))
    
    # 3. Удаляем все записи категорий
    session.exec(text("DELETE FROM categories"))
    
    session.commit()
    return None


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(category_id: int, session: Session = Depends(get_session)):
    """Удалить конкретную категорию"""
    category = session.get(Category, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with id {category_id} not found"
        )

    session.delete(category)
    session.commit()
