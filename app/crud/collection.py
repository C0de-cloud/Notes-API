from datetime import datetime
from typing import Optional, List, Dict, Any
from bson.objectid import ObjectId

from ..db.mongodb import get_database
from ..models.collection import CollectionCreate, CollectionUpdate


async def get_collection_by_id(collection_id: str, owner_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Получить коллекцию по ID, опционально проверяя владельца"""
    db = get_database()
    if not ObjectId.is_valid(collection_id):
        return None
    
    query = {"_id": ObjectId(collection_id)}
    if owner_id:
        query["owner_id"] = ObjectId(owner_id)
    
    return await db.collections.find_one(query)


async def get_collections(owner_id: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    """Получить список коллекций пользователя"""
    db = get_database()
    cursor = db.collections.find({"owner_id": ObjectId(owner_id)}).sort([
        ("is_default", -1),
        ("name", 1)
    ]).skip(skip).limit(limit)
    
    collections = await cursor.to_list(length=limit)
    return collections


async def create_collection(collection: CollectionCreate, owner_id: str) -> Dict[str, Any]:
    """Создать новую коллекцию"""
    db = get_database()
    now = datetime.utcnow()
    
    # Если это коллекция по умолчанию, проверим, что у пользователя нет других коллекций по умолчанию
    if collection.is_default:
        default_collection = await db.collections.find_one({
            "owner_id": ObjectId(owner_id),
            "is_default": True
        })
        if default_collection:
            # Снимаем метку с предыдущей коллекции по умолчанию
            await db.collections.update_one(
                {"_id": default_collection["_id"]},
                {"$set": {"is_default": False}}
            )
    
    collection_data = {
        "_id": ObjectId(),
        "name": collection.name,
        "description": collection.description,
        "color": collection.color,
        "is_default": collection.is_default,
        "owner_id": ObjectId(owner_id),
        "note_count": 0,
        "created_at": now,
        "updated_at": now
    }
    
    await db.collections.insert_one(collection_data)
    
    # Преобразуем ObjectId в строки для возврата
    collection_data["_id"] = str(collection_data["_id"])
    collection_data["owner_id"] = str(collection_data["owner_id"])
    
    return collection_data


async def update_collection(collection_id: str, collection_update: CollectionUpdate, owner_id: str) -> Optional[Dict[str, Any]]:
    """Обновить коллекцию"""
    db = get_database()
    
    if not ObjectId.is_valid(collection_id):
        return None
    
    # Проверяем существование коллекции
    collection = await get_collection_by_id(collection_id, owner_id)
    if not collection:
        return None
    
    # Данные для обновления
    update_data = collection_update.dict(exclude_unset=True)
    
    # Обрабатываем флаг is_default
    if "is_default" in update_data and update_data["is_default"] and not collection["is_default"]:
        # Если устанавливаем флаг, снимаем его с других коллекций
        await db.collections.update_many(
            {"owner_id": ObjectId(owner_id), "is_default": True},
            {"$set": {"is_default": False}}
        )
    
    # Добавляем время обновления
    update_data["updated_at"] = datetime.utcnow()
    
    # Обновляем коллекцию
    await db.collections.update_one(
        {"_id": ObjectId(collection_id), "owner_id": ObjectId(owner_id)},
        {"$set": update_data}
    )
    
    # Возвращаем обновленную коллекцию
    return await get_collection_by_id(collection_id, owner_id)


async def delete_collection(collection_id: str, owner_id: str) -> bool:
    """Удалить коллекцию"""
    db = get_database()
    
    if not ObjectId.is_valid(collection_id):
        return False
    
    # Проверяем существование коллекции
    collection = await get_collection_by_id(collection_id, owner_id)
    if not collection:
        return False
    
    # Удаляем коллекцию
    result = await db.collections.delete_one({"_id": ObjectId(collection_id), "owner_id": ObjectId(owner_id)})
    
    if result.deleted_count == 0:
        return False
    
    # Удаляем все записи о связях заметок с этой коллекцией
    await db.collection_notes.delete_many({"collection_id": ObjectId(collection_id)})
    
    return True


async def add_note_to_collection(collection_id: str, note_id: str, owner_id: str) -> bool:
    """Добавить заметку в коллекцию"""
    db = get_database()
    
    if not ObjectId.is_valid(collection_id) or not ObjectId.is_valid(note_id):
        return False
    
    # Проверяем существование коллекции и права на нее
    collection = await get_collection_by_id(collection_id, owner_id)
    if not collection:
        return False
    
    # Проверяем существование заметки и права на нее
    note = await db.notes.find_one({"_id": ObjectId(note_id), "owner_id": ObjectId(owner_id)})
    if not note:
        return False
    
    # Проверяем, есть ли уже такая связь
    existing_link = await db.collection_notes.find_one({
        "collection_id": ObjectId(collection_id),
        "note_id": ObjectId(note_id)
    })
    
    if existing_link:
        return True  # Связь уже существует
    
    # Создаем связь
    await db.collection_notes.insert_one({
        "_id": ObjectId(),
        "collection_id": ObjectId(collection_id),
        "note_id": ObjectId(note_id),
        "added_at": datetime.utcnow()
    })
    
    # Обновляем счетчик заметок в коллекции
    await db.collections.update_one(
        {"_id": ObjectId(collection_id)},
        {"$inc": {"note_count": 1}}
    )
    
    return True


async def remove_note_from_collection(collection_id: str, note_id: str, owner_id: str) -> bool:
    """Удалить заметку из коллекции"""
    db = get_database()
    
    if not ObjectId.is_valid(collection_id) or not ObjectId.is_valid(note_id):
        return False
    
    # Проверяем существование коллекции и права на нее
    collection = await get_collection_by_id(collection_id, owner_id)
    if not collection:
        return False
    
    # Удаляем связь
    result = await db.collection_notes.delete_one({
        "collection_id": ObjectId(collection_id),
        "note_id": ObjectId(note_id)
    })
    
    if result.deleted_count == 0:
        return False
    
    # Обновляем счетчик заметок в коллекции
    await db.collections.update_one(
        {"_id": ObjectId(collection_id)},
        {"$inc": {"note_count": -1}}
    )
    
    return True


async def get_collection_with_notes(collection_id: str, owner_id: str, skip: int = 0, limit: int = 50) -> Optional[Dict[str, Any]]:
    """Получить коллекцию вместе с заметками"""
    db = get_database()
    
    if not ObjectId.is_valid(collection_id):
        return None
    
    # Получаем коллекцию
    collection = await get_collection_by_id(collection_id, owner_id)
    if not collection:
        return None
    
    # Получаем ID заметок в коллекции
    links = await db.collection_notes.find({
        "collection_id": ObjectId(collection_id)
    }).to_list(length=1000)
    
    note_ids = [link["note_id"] for link in links]
    
    # Если нет заметок, возвращаем пустой список
    if not note_ids:
        collection["notes"] = []
        return collection
    
    # Получаем заметки
    notes = await db.notes.find({
        "_id": {"$in": note_ids},
        "owner_id": ObjectId(owner_id)
    }).sort([
        ("is_pinned", -1),
        ("updated_at", -1)
    ]).skip(skip).limit(limit).to_list(length=limit)
    
    # Преобразуем ObjectId в строки
    for note in notes:
        note["_id"] = str(note["_id"])
        note["owner_id"] = str(note["owner_id"])
        note["tags"] = [str(tag) for tag in note.get("tags", [])]
    
    collection["notes"] = notes
    
    return collection 