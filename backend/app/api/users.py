from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.api import deps
from app.models.user import User
from app.models.role import Role, Permission
from app.models.employee import Employee
from app.schemas.user import (
    UserRead, UserCreate, UserUpdate, 
    RoleRead, PermissionRead, RoleCreate, RoleUpdate, RolePermissionUpdate
)
from app.core.security import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_user_me(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Получение профиля текущего пользователя"""
    user_read = UserRead.model_validate(current_user)
    user_read.is_courier = deps.check_is_courier(current_user, db)
    return user_read


@router.patch("/me", response_model=UserRead)
def update_user_me(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserUpdate,
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Обновление профиля текущего пользователя"""
    update_data = user_in.model_dump(exclude_unset=True)
    
    # Защита от изменения критических полей обычными пользователями
    if not current_user.is_superuser:
        update_data.pop("role_id", None)
        update_data.pop("is_active", None)
        update_data.pop("iiko_id", None)
        
    if "password" in update_data and update_data["password"]:
        password = update_data.pop("password")
        current_user.hashed_password = get_password_hash(password)
        
    for field, value in update_data.items():
        setattr(current_user, field, value)
        
    db.add(current_user)
    db.commit()
    db.refresh(current_user)
    return current_user


@router.get("/", response_model=List[UserRead])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.require_permission("users_view")),
) -> Any:
    """Получение списка всех пользователей (только для админа)"""
    users = db.exec(
        select(User)
        .options(selectinload(User.employee), selectinload(User.role))
        .offset(skip)
        .limit(limit)
    ).all()
    return users


@router.get("/employees")
def get_linkable_employees(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("users_view")),
) -> Any:
    """Список всех сотрудников iiko для привязки к аккаунту"""
    employees = db.exec(select(Employee).where(Employee.status == "Active").order_by(Employee.name)).all()
    # Возвращаем в формате, который ожидает фронтенд (data.data)
    return {"status": "success", "data": employees}


@router.post("/", response_model=UserRead)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.require_permission("users_edit")),
) -> Any:
    """Создание нового пользователя"""
    user = db.exec(select(User).where(User.username == user_in.username)).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким именем уже существует",
        )
    
    # Создаем объект пользователя из данных схемы
    user_data = user_in.model_dump()
    password = user_data.pop("password")
    
    # Явно извлекаем поля, чтобы избежать AttributeError если Pydantic ведет себя странно
    db_obj = User(
        username=user_data.get("username"),
        email=user_data.get("email"),
        full_name=user_data.get("full_name"),
        hashed_password=get_password_hash(password),
        is_active=user_data.get("is_active", True),
        role_id=user_data.get("role_id"),
        iiko_id=user_data.get("iiko_id"),
        is_superuser=False
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj



@router.patch("/{user_id}", response_model=UserRead)
def update_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    user_in: UserUpdate,
    current_user: User = Depends(deps.require_permission("users_edit")),
) -> Any:
    """Обновление пользователя"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        password = update_data.pop("password")
        user.hashed_password = get_password_hash(password)
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user



@router.delete("/{user_id}")
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.require_permission("users_edit")),
) -> Any:
    """Удаление пользователя"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    if user.id == current_user.id:
        raise HTTPException(status_code=400, detail="Нельзя удалить самого себя")
    if user.username == "0001":
        raise HTTPException(status_code=400, detail="Нельзя удалить системного администратора")
    
    db.delete(user)
    db.commit()
    return user


# ============= Управление ролями =============

@router.get("/roles", response_model=List[RoleRead])
def read_roles(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("roles_view")),
) -> Any:
    """Список всех ролей с правами"""
    return db.exec(select(Role).options(selectinload(Role.permissions))).all()


@router.post("/roles", response_model=RoleRead)
def create_role(
    *,
    db: Session = Depends(deps.get_db),
    role_in: RoleCreate,
    current_user: User = Depends(deps.require_permission("roles_edit")),
) -> Any:
    """Создание новой роли"""
    db_obj = Role(**role_in.model_dump())
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@router.patch("/roles/{role_id}", response_model=RoleRead)
def update_role(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    role_in: RoleUpdate,
    current_user: User = Depends(deps.require_permission("roles_edit")),
) -> Any:
    """Обновление данных роли"""
    db_obj = db.get(Role, role_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    update_data = role_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj


@router.delete("/roles/{role_id}", response_model=RoleRead)
def delete_role(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    current_user: User = Depends(deps.require_permission("roles_edit")),
) -> Any:
    """Удаление роли"""
    db_obj = db.get(Role, role_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    if db_obj.is_system:
        raise HTTPException(status_code=400, detail="Нельзя удалить системную роль")
    
    db.delete(db_obj)
    db.commit()
    return db_obj


@router.post("/roles/{role_id}/permissions")
def update_role_permissions(
    *,
    db: Session = Depends(deps.get_db),
    role_id: int,
    perm_in: RolePermissionUpdate,
    current_user: User = Depends(deps.require_permission("roles_edit")),
) -> Any:
    """Обновление прав для роли"""
    db_obj = db.get(Role, role_id)
    if not db_obj:
        raise HTTPException(status_code=404, detail="Роль не найдена")
    
    # Получаем список объектов прав по ID
    permissions = db.exec(select(Permission).where(Permission.id.in_(perm_in.permission_ids))).all()
    
    # Обновляем связи
    db_obj.permissions = permissions
    db.add(db_obj)
    db.commit()
    
    return {"status": "success", "message": "Права обновлены"}


@router.get("/permissions", response_model=List[PermissionRead])
def read_permissions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("roles_view")),
) -> Any:
    """Список всех доступных прав"""
    return db.exec(select(Permission)).all()


@router.post("/sync-iiko-roles")
async def sync_iiko_roles(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.require_permission("roles_edit")),
) -> Any:
    """Принудительная синхронизация ролей из iiko"""
    from app.services.iiko_sync_service import iiko_sync_service
    return await iiko_sync_service.sync_roles(db)
