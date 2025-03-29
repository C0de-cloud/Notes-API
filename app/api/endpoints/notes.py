from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import HTMLResponse, PlainTextResponse, StreamingResponse
from typing import Annotated, List, Optional
from datetime import datetime
import markdown
import io
from weasyprint import HTML

from app.models.note import Note, NoteCreate, NoteUpdate, NoteWithTags, ExportFormat
from app.models.user import User
from app.core.dependencies import get_current_user
from app.crud.note import (
    get_note_by_id, 
    get_notes, 
    create_note, 
    update_note, 
    delete_note,
    get_shared_notes
)

router = APIRouter()


@router.get("", response_model=List[Note])
async def read_notes(
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    tag_ids: Optional[List[str]] = Query(None),
    search: Optional[str] = Query(None),
    pinned: bool = Query(False),
    collection_id: Optional[str] = Query(None)
):
    """
    Получение списка заметок с фильтрацией и пагинацией
    """
    notes = await get_notes(
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
        tag_ids=tag_ids,
        search_text=search,
        pinned_only=pinned,
        collection_id=collection_id
    )
    
    return notes


@router.post("", response_model=Note, status_code=status.HTTP_201_CREATED)
async def create_new_note(
    note_data: NoteCreate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Создание новой заметки
    """
    return await create_note(note_data, current_user.id)


@router.get("/shared-with-me", response_model=List[Note])
async def read_shared_notes(
    current_user: Annotated[User, Depends(get_current_user)],
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Получение списка заметок, к которым текущий пользователь имеет доступ
    """
    return await get_shared_notes(current_user.id, skip, limit)


@router.get("/search", response_model=List[Note])
async def search_notes(
    current_user: Annotated[User, Depends(get_current_user)],
    query: str = Query(..., min_length=1),
    tags: Optional[List[str]] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100)
):
    """
    Поиск заметок по тексту и/или тегам
    """
    notes = await get_notes(
        owner_id=current_user.id,
        skip=skip,
        limit=limit,
        tag_ids=tags,
        search_text=query
    )
    
    return notes


@router.get("/{note_id}", response_model=Note)
async def read_note(
    note_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Получение заметки по ID
    """
    note = await get_note_by_id(note_id, current_user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена"
        )
    return note


@router.put("/{note_id}", response_model=Note)
async def update_note_by_id(
    note_id: str,
    note_data: NoteUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Обновление заметки
    """
    updated_note = await update_note(note_id, note_data, current_user.id)
    if not updated_note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена"
        )
    return updated_note


@router.delete("/{note_id}", status_code=204)
async def delete_note_by_id(
    note_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Удаление заметки
    """
    success = await delete_note(note_id, current_user.id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена"
        )
    return


@router.get("/{note_id}/export/{format}")
async def export_note(
    note_id: str,
    format: ExportFormat,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Экспорт заметки в указанном формате
    """
    note = await get_note_by_id(note_id, current_user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена"
        )
    
    content = note["content"]
    title = note["title"]
    
    if format == ExportFormat.HTML:
        html_content = f"<h1>{title}</h1>"
        if note["format"] == "markdown":
            html_content += markdown.markdown(content)
        else:
            html_content += f"<pre>{content}</pre>"
        
        return HTMLResponse(
            content=html_content,
            headers={"Content-Disposition": f"attachment; filename={note_id}.html"}
        )
    
    elif format == ExportFormat.PDF:
        html_content = f"<h1>{title}</h1>"
        if note["format"] == "markdown":
            html_content += markdown.markdown(content)
        else:
            html_content += f"<pre>{content}</pre>"
        
        pdf = HTML(string=html_content).write_pdf()
        
        return StreamingResponse(
            io.BytesIO(pdf),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={note_id}.pdf"}
        )
    
    elif format == ExportFormat.MARKDOWN:
        if note["format"] == "markdown":
            return PlainTextResponse(
                content=f"# {title}\n\n{content}",
                headers={"Content-Disposition": f"attachment; filename={note_id}.md"}
            )
        else:
            return PlainTextResponse(
                content=f"# {title}\n\n```\n{content}\n```",
                headers={"Content-Disposition": f"attachment; filename={note_id}.md"}
            )
    
    elif format == ExportFormat.TEXT:
        return PlainTextResponse(
            content=f"{title}\n\n{content}",
            headers={"Content-Disposition": f"attachment; filename={note_id}.txt"}
        )
        
    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Формат {format} не поддерживается"
    ) 