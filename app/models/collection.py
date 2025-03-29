from typing import Optional, List
from datetime import datetime
from pydantic import BaseModel, Field


class CollectionBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = None
    is_default: bool = False


class CollectionCreate(CollectionBase):
    pass


class CollectionUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    color: Optional[str] = None
    is_default: Optional[bool] = None


class Collection(CollectionBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    note_count: int = 0
    
    class Config:
        orm_mode = True


class NotesInCollection(BaseModel):
    note_ids: List[str]


class CollectionWithNotes(Collection):
    notes: List[dict] = [] 