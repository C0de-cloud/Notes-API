from fastapi import APIRouter, Depends, HTTPException, status, Query, Path
from typing import Annotated, List, Optional
from datetime import datetime

from app.models.share import Share, ShareRequest, ShareUpdate, ShareResponse, SharePermission
from app.models.user import User
from app.core.dependencies import get_current_user
from app.crud.share import (
    create_share,
    get_share_by_id,
    update_share_permission,
    delete_share,
    get_shares_for_note
)
from app.crud.user import get_user_by_id
from app.crud.note import get_note_by_id

router = APIRouter()


@router.post("/{note_id}/share", response_model=ShareResponse)
async def share_note(
    note_id: str,
    share_data: ShareRequest,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Предоставление доступа к заметке другим пользователям
    """
    note = await get_note_by_id(note_id, current_user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена или у вас нет прав для ее совместного использования"
        )
    
    if str(note["owner_id"]) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав для предоставления доступа к этой заметке"
        )
    
    success_shares = []
    failed_users = []
    
    for user_id in share_data.user_ids:
        target_user = await get_user_by_id(user_id)
        if not target_user:
            failed_users.append(user_id)
            continue
            
        if user_id == current_user.id:
            failed_users.append(user_id)
            continue
            
        try:
            share = await create_share(
                note_id=note_id,
                user_id=user_id,
                permission=share_data.permission
            )
            success_shares.append(share)
        except Exception:
            failed_users.append(user_id)
    
    if failed_users:
        message = f"Доступ предоставлен {len(success_shares)} пользователям. {len(failed_users)} не получилось."
    else:
        message = f"Доступ успешно предоставлен {len(success_shares)} пользователям."
    
    return ShareResponse(
        success=len(success_shares) > 0,
        message=message,
        shares=success_shares
    )


@router.get("/{note_id}/share", response_model=List[Share])
async def get_note_shares(
    note_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Получение списка пользователей, с которыми расшарена заметка
    """
    note = await get_note_by_id(note_id, current_user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена или у вас нет прав для просмотра информации о ней"
        )
    
    if str(note["owner_id"]) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав для просмотра этой информации"
        )
    
    return await get_shares_for_note(note_id)


@router.put("/{note_id}/share/{share_id}", response_model=Share)
async def update_share_by_id(
    note_id: str,
    share_id: str,
    share_data: ShareUpdate,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Обновление разрешений для доступа к заметке
    """
    note = await get_note_by_id(note_id, current_user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена или у вас нет прав для изменения доступа"
        )
    
    if str(note["owner_id"]) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав для изменения доступа к этой заметке"
        )
    
    share = await get_share_by_id(share_id)
    if not share:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись о доступе не найдена"
        )
    
    if str(share["note_id"]) != note_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Запись о доступе не относится к указанной заметке"
        )
    
    updated_share = await update_share_permission(
        share_id=share_id,
        permission=share_data.permission
    )
    
    return updated_share


@router.delete("/{note_id}/share/{user_id}", status_code=204)
async def remove_share(
    note_id: str,
    user_id: str,
    current_user: Annotated[User, Depends(get_current_user)]
):
    """
    Отмена доступа к заметке для указанного пользователя
    """
    note = await get_note_by_id(note_id, current_user.id)
    if not note:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Заметка не найдена или у вас нет прав для изменения доступа"
        )
    
    if str(note["owner_id"]) != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="У вас нет прав для изменения доступа к этой заметке"
        )
    
    success = await delete_share(note_id, user_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Запись о доступе не найдена"
        )
    
    return 