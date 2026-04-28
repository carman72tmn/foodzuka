from typing import Any, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlmodel import Session, select
from app.api import deps
from app.models.user import User
from app.models.role import Role, Permission
from app.schemas.user import UserRead, UserCreate, UserUpdate, RoleRead, PermissionRead
from app.core.security import get_password_hash

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=UserRead)
def read_user_me(
    current_user: User = Depends(deps.get_current_user),
) -> Any:
    """Получение профиля текущего пользователя"""
    return current_user


@router.get("/", response_model=List[UserRead])
def read_users(
    db: Session = Depends(deps.get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Получение списка всех пользователей (только для админа)"""
    users = db.exec(select(User).offset(skip).limit(limit)).all()
    return users


@router.post("/", response_model=UserRead)
def create_user(
    *,
    db: Session = Depends(deps.get_db),
    user_in: UserCreate,
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Создание нового пользователя"""
    user = db.exec(select(User).where(User.username == user_in.username)).first()
    if user:
        raise HTTPException(
            status_code=400,
            detail="Пользователь с таким именем уже существует",
        )
    
    db_obj = User(
        username=user_in.username,
        email=user_in.email,
        full_name=user_in.full_name,
        hashed_password=get_password_hash(user_in.password),
        is_active=user_in.is_active,
        role_id=user_in.role_id,
        iiko_id=user_in.iiko_id,
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
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Обновление пользователя"""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    update_data = user_in.model_dump(exclude_unset=True)
    if "password" in update_data:
        hashed_password = get_password_hash(update_data["password"])
        user.hashed_password = hashed_password
        del update_data["password"]
    
    for field, value in update_data.items():
        setattr(user, field, value)
    
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.delete("/{user_id}", response_model=UserRead)
def delete_user(
    *,
    db: Session = Depends(deps.get_db),
    user_id: int,
    current_user: User = Depends(deps.get_current_active_superuser),
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
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Список всех ролей"""
    return db.exec(select(Role)).all()


@router.get("/permissions", response_model=List[PermissionRead])
def read_permissions(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Список всех доступных прав"""
    return db.exec(select(Permission)).all()


@router.post("/sync-iiko-roles")
async def sync_iiko_roles(
    db: Session = Depends(deps.get_db),
    current_user: User = Depends(deps.get_current_active_superuser),
) -> Any:
    """Принудительная синхронизация ролей из iiko"""
    from app.services.iiko_sync_service import iiko_sync_service
    return await iiko_sync_service.sync_roles(db)
