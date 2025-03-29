from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field


class TagBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    color: Optional[str] = None


class TagCreate(TagBase):
    pass


class TagUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = None


class Tag(TagBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    note_count: Optional[int] = 0
    
    class Config:
        orm_mode = True 