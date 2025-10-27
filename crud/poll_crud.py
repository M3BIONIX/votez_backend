from typing import Sequence, Optional, Dict, Any
from uuid import UUID
from sqlalchemy import insert, update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager
from models import Poll, PollOptions
from models import UserModel
from schemas.poll_schema import PollOptionSchema


class PollCrud:
    def __init__(self):
        self.table = Poll

    async def create_poll(self, session: AsyncSession, poll_data: dict) -> Poll:
        stmt = insert(Poll).values(**poll_data).returning(Poll)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def get_poll_by_uuid(self, session: AsyncSession, poll_uuid: UUID) -> Optional[Poll]:
        stmt = (
            select(Poll)
            .outerjoin(PollOptions, (Poll.id == PollOptions.poll_id) & (PollOptions.is_active == True))
            .where(Poll.uuid == poll_uuid, Poll.is_active == True)
            .options(contains_eager(Poll.poll_options))
        )
        result = await session.execute(stmt)
        return result.scalars().unique().first()

    async def get_all_active_polls(self, session: AsyncSession) -> Sequence[Poll]:
        stmt = (
            select(Poll)
            .outerjoin(PollOptions, (Poll.id == PollOptions.poll_id) & (PollOptions.is_active == True))
            .where(Poll.is_active == True)
            .options(contains_eager(Poll.poll_options))
            .order_by(Poll.created_at.desc())
        )
        result = await session.execute(stmt)
        return result.scalars().unique().all()

    async def update_poll(self, session: AsyncSession, poll_id: int, poll_data: dict) -> Poll:
        stmt = update(Poll).where(Poll.id == poll_id).values(**poll_data).returning(Poll)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def soft_delete_poll(self, session: AsyncSession, poll_id: int) -> Poll:
        stmt = update(Poll).where(Poll.id == poll_id).values(is_active=False).returning(Poll)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_creator_uuid(self, session: AsyncSession, created_by: int) -> Optional[UUID]:
        creator_result = await session.execute(
            select(UserModel).where(UserModel.id == created_by)
        )
        creator = creator_result.scalars().first()
        return creator.uuid if creator else None
    
    async def build_poll_response_data(
        self, 
        session: AsyncSession, 
        poll: Poll,
        current_user_uuid: Optional[UUID] = None
    ) -> Dict[str, Any]:
        from crud.vote_crud import vote_crud as VoteCrud
        from schemas.poll_schema import PollSummaryData

        if current_user_uuid is None:
            current_user_uuid = await self.get_creator_uuid(session, poll.created_by)
        
        # Get actual vote counts from the Vote table
        vote_counts = await VoteCrud.get_vote_counts_by_poll(session, poll.id)
        
        # Sort options by id (ascending order) and build options list with actual vote counts
        sorted_options = sorted(poll.poll_options, key=lambda opt: opt.id)
        options_list = []
        for opt in sorted_options:
            option_data = PollOptionSchema.model_validate(opt).model_dump(mode="json")
            # Replace the stored votes field with actual vote count from Vote table
            option_data["votes"] = vote_counts.get(opt.id, 0)
            options_list.append(option_data)
        
        # Calculate vote summary (total votes and percentages)
        total_votes, option_percentages = await VoteCrud.get_vote_percentages(
            session, poll.id, poll.poll_options
        )
        
        response_dict = {
            "uuid": poll.uuid,
            "title": poll.title,
            "likes": poll.likes,
            "created_at": poll.created_at,
            "version_id": poll.version_id,
            "created_by_uuid": current_user_uuid,
            "options": options_list
        }
        
        # Only include summary if there are votes
        if total_votes > 0:
            summary = PollSummaryData(
                total_votes=total_votes,
                option_percentages=option_percentages
            )
            response_dict["summary"] = summary.model_dump()
        
        return response_dict


poll_crud = PollCrud()