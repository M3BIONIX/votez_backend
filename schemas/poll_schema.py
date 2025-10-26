from datetime import datetime
from typing import List, Optional, Dict
from uuid import UUID
from pydantic import BaseModel, Field

class PollOptionSchema(BaseModel):
    id: int
    option_name: str = Field(..., min_length=1, max_length=200)
    votes: int
    poll_id: int
    uuid: UUID
    version_id: int
    created_at: datetime
    
    model_config = {"from_attributes": True}

class CreatePollOptionSchema(BaseModel):
    option_name: str = Field(..., min_length=1, max_length=200)

class UpdatePollOptionSchema(BaseModel):
    uuid: UUID
    version_id: int
    option_name: str = Field(..., min_length=1, max_length=200)

class CreatePollRequestSchema(BaseModel):
    title: str = Field(..., min_length=3, max_length=300)
    options: List[CreatePollOptionSchema] = Field(..., min_length=2, max_length=10)

class UpdatePollRequestSchema(BaseModel):
    title: Optional[str] = Field(None, max_length=300)
    version_id: int
    options: Optional[List[UpdatePollOptionSchema]] = None

class PollResponseSchema(BaseModel):
    uuid: UUID
    title: str
    likes: int
    created_at: datetime
    created_by_uuid: UUID
    options: List[PollOptionSchema]

    model_config = {"from_attributes": True}

class PollResponseWithVersionId(PollResponseSchema):
    version_id: int


class VoteRequestSchema(BaseModel):
    option_uuid: UUID = Field(..., description="UUID of the option to vote for")


class AddPollOptionsRequestSchema(BaseModel):
    options: List[CreatePollOptionSchema] = Field(..., min_length=1, max_length=10)


class DeletePollOptionsRequestSchema(BaseModel):
    option_uuids: List[UUID] = Field(..., min_length=1)


class PollSummaryResponse(BaseModel):
    """Deprecated: Use PollSummaryData instead. Response schema for poll vote summary."""
    poll_uuid: UUID
    total_votes: int
    option_summary: Dict[str, float]  # option_uuid -> percentage


class LikeResponseSchema(BaseModel):
    """Response schema for like/unlike operations."""
    poll_uuid: UUID
    user_id: int
    is_liked: bool


class PollSummaryData(BaseModel):
    """Summary data for poll vote statistics."""
    total_votes: int
    option_percentages: Dict[str, float]  # option_uuid -> percentage


class VoteResponseSchema(BaseModel):
    """Response schema for vote operations with summary."""
    message: str
    poll_uuid: UUID
    option_uuid: UUID
    summary: PollSummaryData
