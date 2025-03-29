from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from typing import Optional, Union

from ..db.mongodb import get_database
from ..models.user import User, UserRole
from ..core.security import decode_token
from ..models.auth import TokenData

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


async def get_current_user(token: str = Depends(oauth2_scheme)) -> User:
    """Проверяет токен и возвращает текущего пользователя"""
    token_data = decode_token(token)
    
    db = get_database()
    user = await db.users.find_one({"_id": token_data.id})
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Пользователь не найден",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.get("is_active", False):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Аккаунт пользователя деактивирован",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    return User(
        id=str(user["_id"]),
        username=user["username"],
        email=user["email"],
        is_active=user["is_active"],
        full_name=user.get("full_name"),
        role=user.get("role", UserRole.USER),
        created_at=user.get("created_at"),
        updated_at=user.get("updated_at")
    )


async def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, активен ли пользователь"""
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Аккаунт пользователя деактивирован"
        )
    return current_user


async def get_admin_user(current_user: User = Depends(get_current_user)) -> User:
    """Проверяет, является ли пользователь администратором"""
    if current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, 
            detail="Недостаточно прав доступа"
        )
    return current_user 