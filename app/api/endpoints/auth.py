from datetime import timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorDatabase
from typing import Annotated, Dict

from app.db.mongodb import get_database
from app.core.config import get_settings
from app.core.security import create_access_token, verify_password, get_password_hash
from app.core.dependencies import get_current_user
from app.crud.user import authenticate_user, create_user, get_user_by_email
from app.models.auth import Token
from app.models.user import UserCreate, User

settings = get_settings()
router = APIRouter()


@router.post("/register", response_model=Token)
async def register_user(
    user_data: UserCreate
):
    """
    Регистрация нового пользователя
    """
    try:
        user = await create_user(user_data)
        
        access_token_data = {
            "sub": user["_id"],
            "username": user["username"],
            "email": user["email"],
            "role": user["role"]
        }
        
        access_token = create_access_token(access_token_data)
        return {"access_token": access_token, "token_type": "bearer"}
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/login", response_model=Token)
async def login(
    username: str,
    password: str
):
    """
    Авторизация пользователя по имени пользователя/email и паролю
    """
    user = await authenticate_user(username, password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_data = {
        "sub": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"]
    }
    
    access_token = create_access_token(access_token_data)
    return {"access_token": access_token, "token_type": "bearer"}


@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
):
    """
    OAuth2 совместимый токен для совместимости с OpenAPI
    """
    user = await authenticate_user(form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Неверное имя пользователя или пароль",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_data = {
        "sub": str(user["_id"]),
        "username": user["username"],
        "email": user["email"],
        "role": user["role"]
    }
    
    access_token = create_access_token(access_token_data)
    return {"access_token": access_token, "token_type": "bearer"}


@router.get("/me", response_model=User)
async def get_current_user_info(
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Получение информации о текущем авторизованном пользователе
    """
    return current_user 