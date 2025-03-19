# -*- coding: utf-8 -*-

from pydantic import BaseModel, Field, field_validator
from typing import Optional
import re
import uuid
from pydantic import EmailStr


class TokenData(BaseModel):
    username: str
    exp: Optional[int] = None


class Token(BaseModel):
    access_token: str
    token_type: str


class User(BaseModel):
    """User model"""
    id: str
    email: str
    username: str
    disabled: bool = False
    is_admin: bool = False  # Default to False


class UserInDB(User):
    hashed_password: str


class GenericItemBase(BaseModel):
    """Base schema for generic data items"""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name')
    @classmethod
    def name_must_be_valid(cls, v):
        if not re.match(r'^[a-zA-Z0-9 _-]+$', v):
            raise ValueError('Name must contain only alphanumeric characters, spaces, underscores, and hyphens')
        return v


class GenericItemCreate(GenericItemBase):
    """Schema for creating a new generic item"""
    id: Optional[str] = None
    
    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        """Validate ID format or generate a new one if not provided"""
        if v is None:
            return str(uuid.uuid4())
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('ID must contain only alphanumeric characters, underscores, and hyphens')
        return v


class GenericItem(GenericItemBase):
    """Schema for a complete generic item with ID"""
    id: str
    
    class Config:
        orm_mode = True


class GenericItemUpdate(BaseModel):
    """Schema for updating a generic item"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    
    @field_validator('name')
    @classmethod
    def name_must_be_valid(cls, v):
        if v is not None and not re.match(r'^[a-zA-Z0-9 _-]+$', v):
            raise ValueError('Name must contain only alphanumeric characters, spaces, underscores, and hyphens')
        return v
    
    class Config:
        orm_mode = True


class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    
    class Config:
        schema_extra = {
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "password": "strongpassword123"
            }
        }


class UserResponse(BaseModel):
    id: str
    email: EmailStr
    username: str
    is_active: bool
    
    class Config:
        schema_extra = {
            "example": {
                "id": "abc@123",
                "email": "user@example.com",
                "username": "johndoe",
                "is_active": True
            }
        }
