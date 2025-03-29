from datetime import datetime
from typing import Optional, List, Dict, Any, Union
from bson.objectid import ObjectId

from ..db.mongodb import get_database
from ..models.note import NoteCreate, NoteUpdate


async def get_note_by_id(note_id: str, owner_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Получить заметку по ID, опционально проверяя владельца"""
    db = get_database()
    if not ObjectId.is_valid(note_id):
        return None
    
    query = {"_id": ObjectId(note_id)}
    if owner_id:
        query["owner_id"] = ObjectId(owner_id)
    
    return await db.notes.find_one(query)


async def get_notes(
    owner_id: str,
    skip: int = 0,
    limit: int = 50,
    tag_ids: Optional[List[str]] = None,
    search_text: Optional[str] = None,
    pinned_only: bool = False,
    collection_id: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Получить список заметок с фильтрацией и пагинацией"""
    db = get_database()
    
    # Базовый запрос - фильтр по владельцу
    query = {"owner_id": ObjectId(owner_id)}
    
    # Дополнительные фильтры
    if tag_ids:
        query["tags"] = {"$in": [ObjectId(tag_id) for tag_id in tag_ids if ObjectId.is_valid(tag_id)]}
    
    if pinned_only:
        query["is_pinned"] = True
    
    if collection_id:
        if not ObjectId.is_valid(collection_id):
            return []
        collection_notes = await db.collection_notes.find(
            {"collection_id": ObjectId(collection_id)}
        ).to_list(length=1000)
        note_ids = [note["note_id"] for note in collection_notes]
        query["_id"] = {"$in": note_ids}
    
    # Текстовый поиск
    if search_text:
        cursor = db.notes.find(
            {"$and": [query, {"$text": {"$search": search_text}}]},
            {"score": {"$meta": "textScore"}}
        ).sort([("score", {"$meta": "textScore"})])
    else:
        # Сортировка - сначала закрепленные, потом по дате обновления
        cursor = db.notes.find(query).sort([
            ("is_pinned", -1),
            ("updated_at", -1)
        ])
    
    # Применяем пагинацию
    cursor = cursor.skip(skip).limit(limit)
    notes = await cursor.to_list(length=limit)
    
    return notes


async def create_note(note: NoteCreate, owner_id: str) -> Dict[str, Any]:
    """Создать новую заметку"""
    db = get_database()
    now = datetime.utcnow()
    
    # Преобразование строковых ID тегов в ObjectId
    tag_ids = []
    if note.tags:
        tag_ids = [ObjectId(tag_id) for tag_id in note.tags if ObjectId.is_valid(tag_id)]
    
    note_data = {
        "_id": ObjectId(),
        "title": note.title,
        "content": note.content,
        "format": note.format,
        "is_pinned": note.is_pinned,
        "tags": tag_ids,
        "color": note.color,
        "metadata": note.metadata,
        "owner_id": ObjectId(owner_id),
        "created_at": now,
        "updated_at": now
    }
    
    await db.notes.insert_one(note_data)
    
    # Если есть теги, увеличиваем счетчик использования для каждого тега
    if tag_ids:
        await db.tags.update_many(
            {"_id": {"$in": tag_ids}},
            {"$inc": {"note_count": 1}}
        )
    
    # Возвращаем созданную заметку
    note_data["_id"] = str(note_data["_id"])
    note_data["owner_id"] = str(note_data["owner_id"])
    note_data["tags"] = [str(tag_id) for tag_id in tag_ids]
    
    return note_data


async def update_note(note_id: str, note_update: NoteUpdate, owner_id: str) -> Optional[Dict[str, Any]]:
    """Обновить заметку"""
    db = get_database()
    
    if not ObjectId.is_valid(note_id):
        return None
    
    # Получаем существующую заметку
    note = await get_note_by_id(note_id, owner_id)
    if not note:
        return None
    
    # Данные для обновления
    update_data = note_update.dict(exclude_unset=True)
    
    # Обработка тегов
    old_tags = note.get("tags", [])
    
    if "tags" in update_data:
        # Преобразование строковых ID тегов в ObjectId
        if update_data["tags"] is not None:
            new_tags = [ObjectId(tag_id) for tag_id in update_data["tags"] if ObjectId.is_valid(tag_id)]
            update_data["tags"] = new_tags
            
            # Определяем удаленные и добавленные теги
            removed_tags = [tag for tag in old_tags if tag not in new_tags]
            added_tags = [tag for tag in new_tags if tag not in old_tags]
            
            # Обновляем счетчики для тегов
            if removed_tags:
                await db.tags.update_many(
                    {"_id": {"$in": removed_tags}},
                    {"$inc": {"note_count": -1}}
                )
            
            if added_tags:
                await db.tags.update_many(
                    {"_id": {"$in": added_tags}},
                    {"$inc": {"note_count": 1}}
                )
    
    # Добавляем время обновления
    update_data["updated_at"] = datetime.utcnow()
    
    # Обновляем заметку
    await db.notes.update_one(
        {"_id": ObjectId(note_id), "owner_id": ObjectId(owner_id)},
        {"$set": update_data}
    )
    
    # Возвращаем обновленную заметку
    return await get_note_by_id(note_id, owner_id)


async def delete_note(note_id: str, owner_id: str) -> bool:
    """Удалить заметку"""
    db = get_database()
    
    if not ObjectId.is_valid(note_id):
        return False
    
    # Получаем заметку перед удалением для обновления тегов
    note = await get_note_by_id(note_id, owner_id)
    if not note:
        return False
    
    # Удаляем заметку
    result = await db.notes.delete_one({"_id": ObjectId(note_id), "owner_id": ObjectId(owner_id)})
    
    if result.deleted_count == 0:
        return False
    
    # Обновляем счетчики для тегов
    tag_ids = note.get("tags", [])
    if tag_ids:
        await db.tags.update_many(
            {"_id": {"$in": tag_ids}},
            {"$inc": {"note_count": -1}}
        )
    
    # Удаляем связи с коллекциями
    await db.collection_notes.delete_many({"note_id": ObjectId(note_id)})
    
    # Удаляем общий доступ
    await db.shared_notes.delete_many({"note_id": ObjectId(note_id)})
    
    return True


async def get_shared_notes(user_id: str, skip: int = 0, limit: int = 50) -> List[Dict[str, Any]]:
    """Получить заметки, к которым пользователь имеет доступ"""
    db = get_database()
    
    # Найти записи о общем доступе для пользователя
    shared_records = await db.shared_notes.find(
        {"user_id": ObjectId(user_id)}
    ).to_list(length=1000)
    
    if not shared_records:
        return []
    
    # Извлечь ID заметок
    note_ids = [record["note_id"] for record in shared_records]
    
    # Получить заметки
    cursor = db.notes.find({"_id": {"$in": note_ids}}).sort([
        ("updated_at", -1)
    ]).skip(skip).limit(limit)
    
    notes = await cursor.to_list(length=limit)
    
    # Добавить информацию о разрешениях
    for note in notes:
        for record in shared_records:
            if record["note_id"] == note["_id"]:
                note["permission"] = record["permission"]
                break
    
    return notes 