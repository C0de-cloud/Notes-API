from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Annotated, List, Optional
from datetime import datetime

from app.models.tag import Tag, TagCreate, TagUpdate
from app.models.note import Note
from app.models.user import User
from app.core.dependencies import get_current_user
from app.crud.tag import (
    get_tag_by_id, 
    get_tag_by_name,
    get_tags, 
    create_tag, 
    update_tag, 
    delete_tag,
    get_notes_by_tag
)

router = APIRouter()


@router.get("", response_model=List[Tag])
async def read_tags(
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500)
):
    """
    Получение списка всех тегов пользователя
    """
    return await get_tags(current_user.id, skip, limit)


@router.post("", response_model=Tag, status_code=status.HTTP_201_CREATED)
async def create_new_tag(
    tag_data: TagCreate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Создание нового тега
    """
    return await create_tag(tag_data, current_user.id)


@router.get("/{tag_id}", response_model=Tag)
async def read_tag(
    tag_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Получение информации о теге по ID
    """
    tag = await get_tag_by_id(tag_id, current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тег не найден"
        )
    return tag


@router.put("/{tag_id}", response_model=Tag)
async def update_tag_by_id(
    tag_id: str,
    tag_data: TagUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Обновление тега
    """
    updated_tag = await update_tag(tag_id, tag_data, current_user.id)
    if not updated_tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тег не найден"
        )
    return updated_tag


@router.delete("/{tag_id}", status_code=204)
async def delete_tag_by_id(
    tag_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Удаление тега
    """
    success = await delete_tag(tag_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Тег не найден"
        )
    return


@router.get("/{tag_name}/notes", response_model=List[Note])
async def read_notes_by_tag(
    tag_name: str,
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Получение всех заметок с указанным тегом
    """
    tag = await get_tag_by_name(tag_name, current_user.id)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Тег '{tag_name}' не найден"
        )
    
    return await get_notes_by_tag(tag["_id"], current_user.id, skip, limit) 