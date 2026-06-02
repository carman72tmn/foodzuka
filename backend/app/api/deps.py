import logging
from typing import Generator
from fastapi import Depends, HTTPException, status, Header
from fastapi.security import OAuth2PasswordBearer
from jose import jwt, JWTError
from pydantic import ValidationError
from sqlmodel import Session, select
from sqlalchemy.orm import selectinload
from app.core.config import settings
from app.core.database import engine
from app.models.user import User
from app.models.role import Role

logger = logging.getLogger(__name__)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"/api/v1/auth/login"
)


def get_db() -> Generator:
    """Генератор сессии базы данных"""
    with Session(engine) as session:
        yield session


def get_current_user(
    db: Session = Depends(get_db),
    token: str = Depends(oauth2_scheme),
    x_device_id: str = Header(None, alias="X-Device-Id")
) -> User:
    """Получение текущего пользователя с проверкой привязки к устройству"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        token_fp: str = payload.get("fp")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Не удалось валидировать учетные данные",
            )
        
        # Логирование для отладки привязки к устройству
        if token_fp or x_device_id:
            logger.info(f"[Auth] User {user_id}: token_fp={token_fp}, header_device_id={x_device_id}")
            
        # Проверка привязки к устройству (если fp был зашит в токен)
        if token_fp and x_device_id and token_fp != x_device_id:
             raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Сессия привязана к другому устройству. Пожалуйста, войдите снова.",
            )
            
    except (JWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Не удалось валидировать учетные данные",
        )
    
    user = db.exec(
        select(User)
        .options(
            selectinload(User.employee), 
            selectinload(User.role).selectinload(Role.permissions)
        )
        .where(User.id == int(user_id))
    ).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Пользователь не найден"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Пользователь неактивен"
        )
    return user


def get_current_active_superuser(
    current_user: User = Depends(get_current_user),
) -> User:
    """Проверка прав суперпользователя"""
    if not current_user.is_superuser:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Недостаточно прав"
        )
    return current_user


def require_permission(permission_code: str):
    """
    Зависимость для проверки наличия конкретного права у пользователя.
    Суперпользователь (is_superuser=True) всегда имеет доступ.
    """
    def _permission_dependency(
        current_user: User = Depends(get_current_user),
    ) -> User:
        if current_user.is_superuser:
            return current_user
        
        if not current_user.role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Пользователю не назначена роль"
            )
        
        # Проверяем наличие права в списке прав роли
        has_permission = any(p.code == permission_code for p in current_user.role.permissions)
        
        if not has_permission:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Недостаточно прав (требуется: {permission_code})"
            )
            
        return current_user
    
    return _permission_dependency
def get_user_from_token(db: Session, token: str) -> User:
    """Получение пользователя из токена (для WebSocket)"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        user_id: str = payload.get("sub")
        if user_id is None:
            raise JWTError()
    except (JWTError, ValidationError):
        raise ValueError("Invalid token")
    
    user = db.exec(
        select(User)
        .options(
            selectinload(User.employee), 
            selectinload(User.role)
        )
        .where(User.id == int(user_id))
    ).first()
    
    if not user or not user.is_active:
        raise ValueError("User not found or inactive")
    return user
