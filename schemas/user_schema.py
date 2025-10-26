from datetime import datetime
from typing import Optional
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field


class UserBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    email: EmailStr = Field(..., max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=6, max_length=72)


class UserLogin(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=72)


class AuthUser(BaseModel):
    id: int
    name: str
    email: str
    uuid: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
    id: int
    name: str
    email: str
    uuid: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[int] = None

