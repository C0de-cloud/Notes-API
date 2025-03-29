from typing import Optional, List
from enum import Enum
from datetime import datetime
from pydantic import BaseModel, EmailStr, Field, validator


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)
    full_name: Optional[str] = None


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=8)
    full_name: Optional[str] = None
    is_active: Optional[bool] = None
    
    @validator('username')
    def username_cannot_be_empty(cls, v):
        if v == "":
            raise ValueError("Имя пользователя не может быть пустым")
        return v


class UserInDB(UserBase):
    id: str
    hashed_password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.USER
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        orm_mode = True


class User(UserBase):
    id: str
    full_name: Optional[str] = None
    role: UserRole
    created_at: datetime
    updated_at: datetime
    
    class Config:
        orm_mode = True


class UserPublic(BaseModel):
    id: str
    username: str
    full_name: Optional[str] = None
    
    class Config:
        orm_mode = True 