from datetime import datetime
from typing import Optional, List, Dict, Any
from bson.objectid import ObjectId

from ..db.mongodb import get_database
from ..models.user import UserCreate, UserUpdate, UserInDB, User, UserRole
from ..core.security import get_password_hash, verify_password


async def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    """Получить пользователя по email"""
    db = get_database()
    return await db.users.find_one({"email": email})


async def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """Получить пользователя по имени пользователя"""
    db = get_database()
    return await db.users.find_one({"username": username})


async def get_user_by_id(user_id: str) -> Optional[Dict[str, Any]]:
    """Получить пользователя по ID"""
    db = get_database()
    if not ObjectId.is_valid(user_id):
        return None
    return await db.users.find_one({"_id": ObjectId(user_id)})


async def get_users(skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """Получить список пользователей с пагинацией"""
    db = get_database()
    cursor = db.users.find().skip(skip).limit(limit)
    users = await cursor.to_list(length=limit)
    return users


async def create_user(user: UserCreate) -> Dict[str, Any]:
    """Создать нового пользователя"""
    db = get_database()
    
    # Проверка существования email
    existing_user = await get_user_by_email(user.email)
    if existing_user:
        raise ValueError("Пользователь с таким email уже существует")
    
    # Проверка существования имени пользователя
    existing_username = await get_user_by_username(user.username)
    if existing_username:
        raise ValueError("Пользователь с таким именем уже существует")
    
    # Создание пользователя
    hashed_password = get_password_hash(user.password)
    now = datetime.utcnow()
    
    user_in_db = UserInDB(
        id=str(ObjectId()),
        email=user.email,
        username=user.username,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_active=True,
        role=UserRole.USER,
        created_at=now,
        updated_at=now
    )
    
    user_data = user_in_db.dict(exclude={"id"})
    user_data["_id"] = ObjectId(user_in_db.id)
    
    await db.users.insert_one(user_data)
    
    return user_data


async def update_user(user_id: str, user_update: UserUpdate) -> Optional[Dict[str, Any]]:
    """Обновить информацию о пользователе"""
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        return None
    
    user = await get_user_by_id(user_id)
    if not user:
        return None
    
    update_data = user_update.dict(exclude_unset=True)
    
    # Проверка email на уникальность, если он изменяется
    if "email" in update_data and update_data["email"] != user["email"]:
        existing_user = await get_user_by_email(update_data["email"])
        if existing_user:
            raise ValueError("Пользователь с таким email уже существует")
    
    # Проверка имени пользователя на уникальность, если оно изменяется
    if "username" in update_data and update_data["username"] != user["username"]:
        existing_username = await get_user_by_username(update_data["username"])
        if existing_username:
            raise ValueError("Пользователь с таким именем уже существует")
    
    # Хеширование пароля, если он изменяется
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    # Добавление метки времени обновления
    update_data["updated_at"] = datetime.utcnow()
    
    await db.users.update_one(
        {"_id": ObjectId(user_id)},
        {"$set": update_data}
    )
    
    return await get_user_by_id(user_id)


async def delete_user(user_id: str) -> bool:
    """Удалить пользователя"""
    db = get_database()
    
    if not ObjectId.is_valid(user_id):
        return False
    
    result = await db.users.delete_one({"_id": ObjectId(user_id)})
    return result.deleted_count > 0


async def authenticate_user(username_or_email: str, password: str) -> Optional[Dict[str, Any]]:
    """Аутентифицировать пользователя"""
    user = await get_user_by_email(username_or_email)
    if not user:
        user = await get_user_by_username(username_or_email)
        if not user:
            return None
    
    if not verify_password(password, user["hashed_password"]):
        return None
    
    return user 