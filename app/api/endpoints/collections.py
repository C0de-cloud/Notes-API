from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import Annotated, List, Optional
from datetime import datetime

from app.models.collection import Collection, CollectionCreate, CollectionUpdate, CollectionWithNotes, NotesInCollection
from app.models.note import Note, ExportFormat
from app.models.user import User
from app.core.dependencies import get_current_user
from app.crud.collection import (
    get_collection_by_id, 
    get_collections, 
    create_collection, 
    update_collection, 
    delete_collection,
    add_note_to_collection,
    remove_note_from_collection,
    get_collection_with_notes
)

router = APIRouter()


@router.get("", response_model=List[Collection])
async def read_collections(
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Получение списка всех коллекций пользователя
    """
    return await get_collections(current_user.id, skip, limit)


@router.post("", response_model=Collection, status_code=status.HTTP_201_CREATED)
async def create_new_collection(
    collection_data: CollectionCreate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Создание новой коллекции
    """
    return await create_collection(collection_data, current_user.id)


@router.get("/{collection_id}", response_model=CollectionWithNotes)
async def read_collection(
    collection_id: str,
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Получение информации о коллекции и ее заметок по ID
    """
    collection = await get_collection_with_notes(collection_id, current_user.id, skip, limit)
    if not collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Коллекция не найдена"
        )
    return collection


@router.put("/{collection_id}", response_model=Collection)
async def update_collection_by_id(
    collection_id: str,
    collection_data: CollectionUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Обновление коллекции
    """
    updated_collection = await update_collection(collection_id, collection_data, current_user.id)
    if not updated_collection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Коллекция не найдена"
        )
    return updated_collection


@router.delete("/{collection_id}", status_code=204)
async def delete_collection_by_id(
    collection_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Удаление коллекции
    """
    success = await delete_collection(collection_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Коллекция не найдена"
        )
    return


@router.post("/{collection_id}/notes", status_code=200)
async def add_notes_to_collection(
    collection_id: str,
    notes_data: NotesInCollection,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Добавление заметок в коллекцию
    """
    for note_id in notes_data.note_ids:
        success = await add_note_to_collection(collection_id, note_id, current_user.id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Не удалось добавить заметку {note_id} в коллекцию"
            )
    
    return {"message": "Заметки успешно добавлены в коллекцию"}


@router.delete("/{collection_id}/notes/{note_id}", status_code=204)
async def remove_note_from_collection_by_id(
    collection_id: str = Path(..., description="ID коллекции"),
    note_id: str = Path(..., description="ID заметки для удаления из коллекции"),
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Удаление заметки из коллекции
    """
    success = await remove_note_from_collection(collection_id, note_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Коллекция или заметка не найдена"
        )
    return 