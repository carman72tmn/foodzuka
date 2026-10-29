"""
API роутер для модуля "Закуп" (версия 2.0)
"""
from typing import List, Optional
import datetime
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlmodel import Session, select
from app.core.database import get_session
from app.models.purchase import Supplier, PurchasePosition, PurchaseList, PurchaseListItem, PurchaseSubcategory, PurchaseListChange
from app.models.user import User
from app.api.deps import require_permission
from app.schemas import (
    SupplierCreate, SupplierUpdate, SupplierResponse,
    PurchasePositionCreate, PurchasePositionUpdate, PurchasePositionResponse,
    PurchaseListCreate, PurchaseListUpdate, PurchaseListResponse,
    PurchaseListItemResponse,
    PurchaseSubcategoryCreate, PurchaseSubcategoryUpdate, PurchaseSubcategoryResponse,
    PurchaseListChangeResponse
)
from app.core.datetime_utils import utc_now
from app.services.vk_notification_router import vk_notification_router

router = APIRouter(prefix="/purchase", tags=["Purchase"])


def get_category_name(category: str) -> str:
    mapping = {
        "supply": "Поставки",
        "shop": "Магазин",
        "household": "Хозка"
    }
    return mapping.get(category, category)


def validate_supplier(supplier_id: Optional[int], session: Session):
    if supplier_id is not None:
        supplier = session.get(Supplier, supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Указанный поставщик с ID={supplier_id} не существует"
            )


# --- Поставщики (Suppliers) ---

@router.get("/suppliers", response_model=List[SupplierResponse])
def get_suppliers(
    is_active: Optional[bool] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_view"))
):
    """Получить список всех поставщиков"""
    query = select(Supplier)
    if is_active is not None:
        query = query.where(Supplier.is_active == is_active)
    query = query.order_by(Supplier.name)
    return session.exec(query).all()


@router.get("/suppliers/{supplier_id}", response_model=SupplierResponse)
def get_supplier(
    supplier_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_view"))
):
    """Получить поставщика по ID"""
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Поставщик не найден"
        )
    return supplier


@router.post("/suppliers", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    data: SupplierCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_edit"))
):
    """Создать нового поставщика"""
    supplier = Supplier(**data.model_dump())
    session.add(supplier)
    session.commit()
    session.refresh(supplier)
    return supplier


@router.patch("/suppliers/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    data: SupplierUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_edit"))
):
    """Обновить информацию о поставщике"""
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Поставщик не найден"
        )
    
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(supplier, key, value)
    
    supplier.updated_at = utc_now()
    session.add(supplier)
    session.commit()
    session.refresh(supplier)
    return supplier


@router.delete("/suppliers/{supplier_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_supplier(
    supplier_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_edit"))
):
    """Удалить поставщика"""
    supplier = session.get(Supplier, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Поставщик не найден"
        )
    session.delete(supplier)
    session.commit()
    return None


# --- Подкатегории закупа (Subcategories) ---

@router.get("/subcategories", response_model=List[PurchaseSubcategoryResponse])
def get_subcategories(
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_view"))
):
    """Получить список всех подкатегорий закупа"""
    query = select(PurchaseSubcategory).order_by(PurchaseSubcategory.name)
    return session.exec(query).all()


@router.post("/subcategories", response_model=PurchaseSubcategoryResponse, status_code=status.HTTP_201_CREATED)
def create_subcategory(
    data: PurchaseSubcategoryCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_edit"))
):
    """Создать новую подкатегорию закупа"""
    existing = session.exec(select(PurchaseSubcategory).where(PurchaseSubcategory.name == data.name)).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Подкатегория с именем '{data.name}' уже существует"
        )
    
    sub = PurchaseSubcategory(**data.model_dump())
    session.add(sub)
    session.commit()
    session.refresh(sub)
    return sub


@router.patch("/subcategories/{subcategory_id}", response_model=PurchaseSubcategoryResponse)
def update_subcategory(
    subcategory_id: int,
    data: PurchaseSubcategoryUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_edit"))
):
    """Обновить имя подкатегории закупа"""
    sub = session.get(PurchaseSubcategory, subcategory_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Подкатегория не найдена"
        )
    
    if data.name:
        existing = session.exec(select(PurchaseSubcategory).where(PurchaseSubcategory.name == data.name, PurchaseSubcategory.id != subcategory_id)).first()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Подкатегория с именем '{data.name}' уже существует"
            )
        sub.name = data.name

    session.add(sub)
    session.commit()
    session.refresh(sub)
    return sub


@router.delete("/subcategories/{subcategory_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subcategory(
    subcategory_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_edit"))
):
    """Удалить подкатегорию закупа"""
    sub = session.get(PurchaseSubcategory, subcategory_id)
    if not sub:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Подкатегория не найдена"
        )
    session.delete(sub)
    session.commit()
    return None


# --- Справочник позиций закупа ---

@router.get("/positions", response_model=List[PurchasePositionResponse])
def get_positions(
    category: Optional[str] = None,
    subcategory: Optional[str] = None,
    supplier_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_view"))
):
    """Получить список всех позиций закупа с фильтрацией"""
    query = select(PurchasePosition)
    if category:
        query = query.where(PurchasePosition.category == category)
    if subcategory:
        query = query.where(PurchasePosition.subcategory == subcategory)
    if supplier_id:
        query = query.where(PurchasePosition.supplier_id == supplier_id)
    if is_active is not None:
        query = query.where(PurchasePosition.is_active == is_active)
    query = query.order_by(PurchasePosition.name)
    return session.exec(query).all()


@router.get("/positions/{position_id}", response_model=PurchasePositionResponse)
def get_position(
    position_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_view"))
):
    """Получить позицию по ID"""
    position = session.get(PurchasePosition, position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция закупа не найдена"
        )
    return position


@router.post("/positions", response_model=PurchasePositionResponse, status_code=status.HTTP_201_CREATED)
def create_position(
    data: PurchasePositionCreate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_edit"))
):
    """Создать новую позицию закупа в справочнике"""
    validate_supplier(data.supplier_id, session)
    position = PurchasePosition(**data.model_dump())
    session.add(position)
    session.commit()
    session.refresh(position)
    return position


@router.patch("/positions/{position_id}", response_model=PurchasePositionResponse)
def update_position(
    position_id: int, 
    data: PurchasePositionUpdate, 
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_edit"))
):
    """Обновить позицию закупа в справочнике"""
    position = session.get(PurchasePosition, position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция закупа не найдена"
        )
    
    validate_supplier(data.supplier_id, session)
    update_data = data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(position, key, value)
    
    position.updated_at = utc_now()
    session.add(position)
    session.commit()
    session.refresh(position)
    return position


@router.delete("/positions/{position_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_position(
    position_id: int, 
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_positions_edit"))
):
    """Удалить позицию закупа из справочника"""
    position = session.get(PurchasePosition, position_id)
    if not position:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Позиция закупа не найдена"
        )
    session.delete(position)
    session.commit()
    return None


# --- Списки закупа ---

class PurchaseListItemUpdateInput(BaseModel):
    position_id: int
    quantity: float
    comment: Optional[str] = None
    is_urgent: Optional[bool] = False
    is_bought: Optional[bool] = False
    
class PurchaseListUpdateInput(BaseModel):
    name: Optional[str] = None
    date: Optional[datetime.date] = None
    status: Optional[str] = None
    items: Optional[List[PurchaseListItemUpdateInput]] = None


@router.get("/lists", response_model=List[PurchaseListResponse])
def get_lists(
    category: Optional[str] = None,
    status: Optional[str] = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_lists_view"))
):
    """Получить список всех листов закупа"""
    query = select(PurchaseList)
    if category:
        query = query.where(PurchaseList.category == category)
    if status:
        query = query.where(PurchaseList.status == status)
    query = query.order_by(PurchaseList.date.desc(), PurchaseList.id.desc())
    
    lists = session.exec(query).all()
    return lists


@router.get("/lists/{list_id}", response_model=PurchaseListResponse)
def get_list(
    list_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_lists_view"))
):
    """Получить список закупа по ID"""
    lst = session.get(PurchaseList, list_id)
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Список закупа не найден"
        )
    return lst


@router.post("/lists", response_model=PurchaseListResponse, status_code=status.HTTP_201_CREATED)
def create_list(
    data: PurchaseListCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_lists_edit"))
):
    """Создать новый список закупа на дату и автоматически добавить все активные позиции"""
    lst = PurchaseList(**data.model_dump())
    lst.created_by_id = current_user.id
    lst.updated_by_id = current_user.id
    session.add(lst)
    session.flush()
    
    # Загружаем все активные позиции данного направления
    pos_query = select(PurchasePosition).where(
        PurchasePosition.category == lst.category,
        PurchasePosition.is_active == True
    )
    positions = session.exec(pos_query).all()
    
    for pos in positions:
        item = PurchaseListItem(
            list_id=lst.id,
            position_id=pos.id,
            quantity=0.0
        )
        session.add(item)
        
    session.flush()
    
    # Запишем лог создания
    change = PurchaseListChange(
        list_id=lst.id,
        user_id=current_user.id,
        action_type="create",
        details="Создан список закупа"
    )
    session.add(change)
    session.commit()
    session.refresh(lst)
    
    return lst


@router.patch("/lists/{list_id}", response_model=PurchaseListResponse)
def update_list(
    list_id: int,
    data: PurchaseListUpdateInput,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_lists_edit"))
):
    """Обновить список закупа и его элементы (пакетно)"""
    lst = session.get(PurchaseList, list_id)
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Список закупа не найден"
        )
        
    changes_list = []
    
    # Сравниваем метаданные
    if data.name is not None and data.name != lst.name:
        changes_list.append(f"Изменено название с '{lst.name}' на '{data.name}'")
        lst.name = data.name
    if data.date is not None and data.date != lst.date:
        changes_list.append(f"Изменена дата поставки с '{lst.date}' на '{data.date}'")
        lst.date = data.date
    if data.status is not None and data.status != lst.status:
        status_old = "Черновик" if lst.status == "draft" else "Отправлен"
        status_new = "Черновик" if data.status == "draft" else "Отправлен"
        changes_list.append(f"Изменен статус с '{status_old}' на '{status_new}'")
        lst.status = data.status
        
    if data.items is not None:
        existing_items = {item.position_id: item for item in lst.items}
        for item_input in data.items:
            if item_input.position_id in existing_items:
                item = existing_items[item_input.position_id]
                pos_name = item.position.name if item.position else f"ID={item.position_id}"
                item_changes = []
                
                if item_input.quantity is not None and item_input.quantity != item.quantity:
                    unit_label = item.position.unit if (item.position and item.position.unit) else "шт"
                    item_changes.append(f"количество с {item.quantity} {unit_label} на {item_input.quantity} {unit_label}")
                    item.quantity = item_input.quantity
                    
                if item_input.comment is not None and item_input.comment != item.comment:
                    old_comment = item.comment or "нет"
                    item_changes.append(f"комментарий с '{old_comment}' на '{item_input.comment}'")
                    item.comment = item_input.comment
                    
                if item_input.is_urgent is not None and item_input.is_urgent != item.is_urgent:
                    item_changes.append(f"срочность на {'Да' if item_input.is_urgent else 'Нет'}")
                    item.is_urgent = item_input.is_urgent
                    
                if item_input.is_bought is not None and item_input.is_bought != item.is_bought:
                    item_changes.append(f"статус покупки на {'Куплено' if item_input.is_bought else 'Не куплено'}")
                    item.is_bought = item_input.is_bought
                    
                if item_changes:
                    changes_list.append(f"Обновлен товар '{pos_name}': {', '.join(item_changes)}")
                    item.updated_at = utc_now()
                    session.add(item)
            else:
                pos = session.get(PurchasePosition, item_input.position_id)
                pos_name = pos.name if pos else f"ID={item_input.position_id}"
                new_item = PurchaseListItem(
                    list_id=lst.id,
                    position_id=item_input.position_id,
                    quantity=item_input.quantity,
                    comment=item_input.comment,
                    is_urgent=item_input.is_urgent or False,
                    is_bought=item_input.is_bought or False
                )
                session.add(new_item)
                changes_list.append(f"Добавлен товар '{pos_name}' в количестве {item_input.quantity}")
                
    if changes_list:
        lst.updated_by_id = current_user.id
        lst.updated_at = utc_now()
        session.add(lst)
        
        # Создаем запись истории изменений
        change = PurchaseListChange(
            list_id=lst.id,
            user_id=current_user.id,
            action_type="update_items" if data.items is not None else "update_meta",
            details="; \n".join(changes_list)
        )
        session.add(change)
        session.commit()
    else:
        # Если изменений не было, просто сохраним системную дату
        lst.updated_at = utc_now()
        session.add(lst)
        session.commit()
        
    session.refresh(lst)
    return lst


@router.delete("/lists/{list_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_list(
    list_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_lists_edit"))
):
    """Удалить список закупа"""
    lst = session.get(PurchaseList, list_id)
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Список закупа не найден"
        )
    session.delete(lst)
    session.commit()
    return None


@router.get("/lists/{list_id}/changes", response_model=List[PurchaseListChangeResponse])
def get_list_changes(
    list_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_lists_view"))
):
    """Получить историю изменений списка закупа"""
    query = select(PurchaseListChange).where(PurchaseListChange.list_id == list_id).order_by(PurchaseListChange.created_at.desc())
    return session.exec(query).all()


@router.post("/lists/{list_id}/items/{position_id}/toggle_bought", response_model=PurchaseListItemResponse)
def toggle_item_bought(
    list_id: int,
    position_id: int,
    is_bought: bool,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_lists_edit"))
):
    """Быстро переключить статус покупки элемента списка закупа (куплен / не куплен)"""
    lst = session.get(PurchaseList, list_id)
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Список закупа не найден"
        )
        
    query = select(PurchaseListItem).where(
        PurchaseListItem.list_id == list_id,
        PurchaseListItem.position_id == position_id
    )
    item = session.exec(query).first()
    if not item:
        item = PurchaseListItem(
            list_id=list_id,
            position_id=position_id,
            quantity=0.0,
            is_bought=is_bought
        )
        session.add(item)
        session.flush()
    else:
        item.is_bought = is_bought
        item.updated_at = utc_now()
        session.add(item)
        
    # Запишем лог изменений
    pos_name = item.position.name if item.position else f"ID={position_id}"
    status_text = "куплен" if is_bought else "не куплен"
    details = f"Товар '{pos_name}' отмечен как {status_text}"
    
    lst.updated_by_id = current_user.id
    lst.updated_at = utc_now()
    session.add(lst)
    
    change = PurchaseListChange(
        list_id=list_id,
        user_id=current_user.id,
        action_type="toggle_bought",
        details=details
    )
    session.add(change)
    session.commit()
    session.refresh(item)
    return item


@router.post("/lists/{list_id}/send", response_model=PurchaseListResponse)
async def send_purchase_list(
    list_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(require_permission("purchase_lists_edit"))
):
    """Отправить сформированный список закупа через системные рассылки"""
    lst = session.get(PurchaseList, list_id)
    if not lst:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Список закупа не найден"
        )
        
    active_items = [item for item in lst.items if item.quantity > 0]
    
    grouped = defaultdict(list)
    for item in active_items:
        subcat = item.position.subcategory or "Без категории"
        grouped[subcat].append(item)
        
    lines = []
    for subcat in sorted(grouped.keys()):
        lines.append(f"📁 {subcat}:")
        for item in grouped[subcat]:
            pos = item.position
            supplier_info = f" (Поставщик: {pos.supplier.name})" if pos.supplier else ""
            comment_info = f" [{item.comment}]" if item.comment else ""
            urgent_info = " 🚨 СРОЧНО!" if item.is_urgent else ""
            lines.append(f"  - {pos.name}: {item.quantity} {pos.unit or 'шт'}{supplier_info}{comment_info}{urgent_info}")
        lines.append("")
        
    items_summary_text = "\n".join(lines).strip()
    if not items_summary_text:
        items_summary_text = "Нет позиций к закупу."
        
    context = {
        "purchase_list": {
            "name": lst.name,
            "category_name": get_category_name(lst.category),
            "date": lst.date.strftime('%d.%m.%Y') if lst.date else '',
            "items_summary": items_summary_text
        }
    }
    
    default_message = (
        f"📦 Отправлен список закупа: {lst.name}\n"
        f"Направление: {get_category_name(lst.category)}\n"
        f"Дата поставки: {lst.date.strftime('%d.%m.%Y') if lst.date else ''}\n\n"
        f"Позиции к закупу:\n{items_summary_text}"
    )
    
    # Отправляем уведомление
    await vk_notification_router.dispatch_event(
        event_type="purchase_list_sent",
        message_text=default_message,
        context_data=context
    )
    
    lst.status = "sent"
    lst.updated_at = utc_now()
    session.add(lst)
    session.commit()
    session.refresh(lst)
    return lst
