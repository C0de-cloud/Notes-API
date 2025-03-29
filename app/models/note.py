from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum
from pydantic import BaseModel, Field


class NoteFormat(str, Enum):
    MARKDOWN = "markdown"
    PLAIN = "plain"


class NoteBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    content: str = Field(..., min_length=1)
    format: NoteFormat = NoteFormat.MARKDOWN
    is_pinned: bool = False
    tags: List[str] = []
    color: Optional[str] = None
    metadata: Dict[str, Any] = {}


class NoteCreate(NoteBase):
    pass


class NoteUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    content: Optional[str] = Field(None, min_length=1)
    format: Optional[NoteFormat] = None
    is_pinned: Optional[bool] = None
    tags: Optional[List[str]] = None
    color: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class Note(NoteBase):
    id: str
    owner_id: str
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class NoteWithTags(Note):
    tag_objects: List[Dict[str, Any]] = []


class ExportFormat(str, Enum):
    HTML = "html"
    PDF = "pdf"
    TEXT = "text"
    MARKDOWN = "markdown"


class NoteExport(BaseModel):
    note_ids: List[str]
    format: ExportFormat = ExportFormat.HTML
    include_metadata: bool = False 