from datetime import datetime
from typing import List, Optional
from uuid import UUID
from pydantic import BaseModel, Field

class PollOptionSchema(BaseModel):
    id: int
    option_name: str = Field(..., min_length=1, max_length=200)
    votes: int
    poll_id: int
    uuid: UUID
    created_at: datetime
    
    model_config = {"from_attributes": True}

class CreatePollOptionSchema(BaseModel):
    option_text: str = Field(..., min_length=1, max_length=200)

class UpdatePollOptionSchema(BaseModel):
    uuid: UUID
    version_id: int
    option_text: str = Field(..., min_length=1, max_length=200)

class CreatePollRequestSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    options: List[CreatePollOptionSchema] = Field(..., min_length=2, max_length=10)

class UpdatePollRequestSchema(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=300)
    options: Optional[List[UpdatePollOptionSchema]] = Field(None, min_length=1, max_length=10)

class PollResponseSchema(BaseModel):
    uuid: UUID
    title: str
    likes: int
    created_at: datetime
    options: List[PollOptionSchema]

    model_config = {"from_attributes": True}
