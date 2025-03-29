from datetime import datetime
from typing import Optional, List, Dict, Any
from bson.objectid import ObjectId

from ..db.mongodb import get_database
from ..models.tag import TagCreate, TagUpdate


async def get_tag_by_id(tag_id: str, owner_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Получить тег по ID, опционально проверяя владельца"""
    db = get_database()
    if not ObjectId.is_valid(tag_id):
        return None
    
    query = {"_id": ObjectId(tag_id)}
    if owner_id:
        query["owner_id"] = ObjectId(owner_id)
    
    return await db.tags.find_one(query)


async def get_tag_by_name(tag_name: str, owner_id: str) -> Optional[Dict[str, Any]]:
    """Получить тег по имени и владельцу"""
    db = get_database()
    return await db.tags.find_one({"name": tag_name, "owner_id": ObjectId(owner_id)})


async def get_tags(owner_id: str, skip: int = 0, limit: int = 100) -> List[Dict[str, Any]]:
    """Получить список тегов пользователя"""
    db = get_database()
    cursor = db.tags.find({"owner_id": ObjectId(owner_id)}).sort([
        ("name", 1)
    ]).skip(skip).limit(limit)
    
    tags = await cursor.to_list(length=limit)
    return tags


async def create_tag(tag: TagCreate, owner_id: str) -> Dict[str, Any]:
    """Создать новый тег"""
    db = get_database()
    
    # Проверяем, существует ли тег с таким названием у пользователя
    existing_tag = await get_tag_by_name(tag.name, owner_id)
    if existing_tag:
        raise ValueError(f"Тег с названием '{tag.name}' уже существует")
    
    now = datetime.utcnow()
    tag_data = {
        "_id": ObjectId(),
        "name": tag.name,
        "color": tag.color,
        "owner_id": ObjectId(owner_id),
        "note_count": 0,
        "created_at": now,
        "updated_at": now
    }
    
    await db.tags.insert_one(tag_data)
    
    # Преобразуем ObjectId в строки для возврата
    tag_data["_id"] = str(tag_data["_id"])
    tag_data["owner_id"] = str(tag_data["owner_id"])
    
    return tag_data


async def update_tag(tag_id: str, tag_update: TagUpdate, owner_id: str) -> Optional[Dict[str, Any]]:
    """Обновить тег"""
    db = get_database()
    
    if not ObjectId.is_valid(tag_id):
        return None
    
    # Проверяем существование тега
    tag = await get_tag_by_id(tag_id, owner_id)
    if not tag:
        return None
    
    # Данные для обновления
    update_data = tag_update.dict(exclude_unset=True)
    
    # Проверяем уникальность имени, если оно меняется
    if "name" in update_data and update_data["name"] != tag["name"]:
        existing_tag = await get_tag_by_name(update_data["name"], owner_id)
        if existing_tag:
            raise ValueError(f"Тег с названием '{update_data['name']}' уже существует")
    
    # Добавляем время обновления
    update_data["updated_at"] = datetime.utcnow()
    
    # Обновляем тег
    await db.tags.update_one(
        {"_id": ObjectId(tag_id), "owner_id": ObjectId(owner_id)},
        {"$set": update_data}
    )
    
    # Возвращаем обновленный тег
    return await get_tag_by_id(tag_id, owner_id)


async def delete_tag(tag_id: str, owner_id: str) -> bool:
    """Удалить тег"""
    db = get_database()
    
    if not ObjectId.is_valid(tag_id):
        return False
    
    # Получаем тег перед удалением
    tag = await get_tag_by_id(tag_id, owner_id)
    if not tag:
        return False
    
    # Удаляем тег
    result = await db.tags.delete_one({"_id": ObjectId(tag_id), "owner_id": ObjectId(owner_id)})
    
    if result.deleted_count == 0:
        return False
    
    # Удаляем тег из всех заметок пользователя
    await db.notes.update_many(
        {"owner_id": ObjectId(owner_id), "tags": ObjectId(tag_id)},
        {"$pull": {"tags": ObjectId(tag_id)}}
    )
    
    return True


async def get_notes_by_tag(tag_id: str, owner_id: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    """Получить все заметки с указанным тегом"""
    db = get_database()
    
    if not ObjectId.is_valid(tag_id):
        return []
    
    # Находим все заметки пользователя с указанным тегом
    query = {
        "owner_id": ObjectId(owner_id),
        "tags": ObjectId(tag_id)
    }
    
    cursor = db.notes.find(query).sort([
        ("updated_at", -1)
    ]).skip(skip).limit(limit)
    
    notes = await cursor.to_list(length=limit)
    return notes 