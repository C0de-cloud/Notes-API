from datetime import datetime
from typing import Optional, List, Dict, Any
from bson.objectid import ObjectId

from ..db.mongodb import get_database
from ..models.share import SharePermission


async def get_share_by_id(share_id: str) -> Optional[Dict[str, Any]]:
    """Получить запись о совместном доступе по ID"""
    db = get_database()
    if not ObjectId.is_valid(share_id):
        return None
    
    return await db.shared_notes.find_one({"_id": ObjectId(share_id)})


async def get_share(note_id: str, user_id: str) -> Optional[Dict[str, Any]]:
    """Получить запись о совместном доступе по ID заметки и ID пользователя"""
    db = get_database()
    if not ObjectId.is_valid(note_id) or not ObjectId.is_valid(user_id):
        return None
    
    return await db.shared_notes.find_one({
        "note_id": ObjectId(note_id),
        "user_id": ObjectId(user_id)
    })


async def get_shares_for_note(note_id: str) -> List[Dict[str, Any]]:
    """Получить все записи о совместном доступе для заметки"""
    db = get_database()
    if not ObjectId.is_valid(note_id):
        return []
    
    cursor = db.shared_notes.find({"note_id": ObjectId(note_id)})
    shares = await cursor.to_list(length=100)
    
    # Преобразуем ObjectId в строки
    for share in shares:
        share["_id"] = str(share["_id"])
        share["note_id"] = str(share["note_id"])
        share["user_id"] = str(share["user_id"])
    
    return shares


async def create_share(note_id: str, user_id: str, permission: SharePermission = SharePermission.READ) -> Dict[str, Any]:
    """Создать запись о совместном доступе"""
    db = get_database()
    
    if not ObjectId.is_valid(note_id) or not ObjectId.is_valid(user_id):
        raise ValueError("Некорректный ID заметки или пользователя")
    
    # Проверяем существование заметки
    note = await db.notes.find_one({"_id": ObjectId(note_id)})
    if not note:
        raise ValueError("Заметка не найдена")
    
    # Проверяем существование пользователя
    user = await db.users.find_one({"_id": ObjectId(user_id)})
    if not user:
        raise ValueError("Пользователь не найден")
    
    # Проверяем, что пользователь не является владельцем заметки
    if note["owner_id"] == ObjectId(user_id):
        raise ValueError("Нельзя предоставить доступ владельцу заметки")
    
    # Проверяем, есть ли уже запись о доступе
    existing_share = await get_share(note_id, user_id)
    if existing_share:
        # Обновляем разрешения, если запись уже существует
        await db.shared_notes.update_one(
            {"_id": existing_share["_id"]},
            {"$set": {"permission": permission, "updated_at": datetime.utcnow()}}
        )
        
        # Возвращаем обновленную запись
        return await get_share(note_id, user_id)
    
    # Создаем новую запись о доступе
    now = datetime.utcnow()
    share_data = {
        "_id": ObjectId(),
        "note_id": ObjectId(note_id),
        "user_id": ObjectId(user_id),
        "permission": permission,
        "created_at": now,
        "updated_at": now
    }
    
    await db.shared_notes.insert_one(share_data)
    
    # Преобразуем ObjectId в строки для возврата
    share_data["_id"] = str(share_data["_id"])
    share_data["note_id"] = str(share_data["note_id"])
    share_data["user_id"] = str(share_data["user_id"])
    
    return share_data


async def update_share_permission(share_id: str, permission: SharePermission) -> Optional[Dict[str, Any]]:
    """Обновить разрешения для записи о совместном доступе"""
    db = get_database()
    
    if not ObjectId.is_valid(share_id):
        return None
    
    # Проверяем существование записи
    share = await get_share_by_id(share_id)
    if not share:
        return None
    
    # Обновляем разрешения
    await db.shared_notes.update_one(
        {"_id": ObjectId(share_id)},
        {"$set": {"permission": permission, "updated_at": datetime.utcnow()}}
    )
    
    # Возвращаем обновленную запись
    return await get_share_by_id(share_id)


async def delete_share(note_id: str, user_id: str) -> bool:
    """Удалить запись о совместном доступе"""
    db = get_database()
    
    if not ObjectId.is_valid(note_id) or not ObjectId.is_valid(user_id):
        return False
    
    # Удаляем запись
    result = await db.shared_notes.delete_one({
        "note_id": ObjectId(note_id),
        "user_id": ObjectId(user_id)
    })
    
    return result.deleted_count > 0 