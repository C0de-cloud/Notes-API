from typing import Optional, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, Field


class SharePermission(str, Enum):
    READ = "read"
    EDIT = "edit"


class ShareBase(BaseModel):
    note_id: str
    user_id: str
    permission: SharePermission = SharePermission.READ


class ShareCreate(ShareBase):
    pass


class ShareUpdate(BaseModel):
    permission: Optional[SharePermission] = None


class Share(ShareBase):
    id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class ShareRequest(BaseModel):
    user_ids: List[str]
    note_id: str
    permission: SharePermission = SharePermission.READ


class ShareResponse(BaseModel):
    success: bool
    message: str
    shares: List[Share] = [] 