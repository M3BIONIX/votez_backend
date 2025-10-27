from datetime import datetime
from typing import Optional, List, Dict
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
    name: str
    email: str
    uuid: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}


class UserResponse(BaseModel):
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


class VotedPollInfo(BaseModel):
    poll_uuid: UUID
    option_uuid: UUID
    total_votes: int
    percentage: float  # percentage of votes for the selected option


class UserMeResponse(BaseModel):
    name: str
    email: str
    uuid: UUID
    created_at: datetime
    liked_poll_uuids: List[UUID] = Field(default_factory=list)
    voted_polls: List[VotedPollInfo] = Field(default_factory=list)
    
    model_config = {"from_attributes": True}

