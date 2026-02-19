from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from uuid import UUID
from datetime import datetime

class UserBase(BaseModel):
    """Shared properties for User models."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    is_active: Optional[bool] = True
    is_superuser: Optional[bool] = False

class UserCreate(UserBase):
    """Properties to receive via API on creation."""
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    """Properties to receive via API on update."""
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    password: Optional[str] = None
    is_active: Optional[bool] = None

class UserResponse(UserBase):
    """Properties to return via API."""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
