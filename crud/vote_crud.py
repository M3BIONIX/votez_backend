from sqlalchemy import select, delete, insert, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence

from models import Vote


class VoteCrud:
    """CRUD operations for Vote model."""
    
    def __init__(self):
        self.table = Vote
    
    async def create_vote(self, session: AsyncSession, user_id: int, poll_id: int, option_id: int) -> Vote:
        """Create a new vote."""
        stmt = insert(Vote).values(
            user_id=user_id,
            poll_id=poll_id,
            option_id=option_id
        ).returning(Vote)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def delete_vote(self, session: AsyncSession, user_id: int, poll_id: int) -> bool:
        """Remove a vote."""
        stmt = delete(Vote).where(
            Vote.user_id == user_id,
            Vote.poll_id == poll_id
        )
        result = await session.execute(stmt)
        return result.rowcount > 0
    
    async def get_vote(self, session: AsyncSession, user_id: int, poll_id: int):
        """Check if user has voted on a poll."""
        stmt = select(Vote).where(
            Vote.user_id == user_id,
            Vote.poll_id == poll_id
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_votes_by_poll(self, session: AsyncSession, poll_id: int) -> Sequence[Vote]:
        """Get all votes for a poll."""
        stmt = select(Vote).where(Vote.poll_id == poll_id)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_vote_counts_by_poll(self, session: AsyncSession, poll_id: int) -> dict:
        """Get vote counts grouped by option for a poll."""
        stmt = select(
            Vote.option_id,
            func.count(Vote.option_id).label("count")
        ).where(
            Vote.poll_id == poll_id
        ).group_by(Vote.option_id)
        
        result = await session.execute(stmt)
        return {row.option_id: row.count for row in result}
    
    async def get_votes_by_user(self, session: AsyncSession, user_id: int):
        """Get votes with poll and option UUIDs for a user."""
        from models import Poll, PollOptions
        
        # Join Vote with Poll and PollOptions to get UUIDs
        stmt = (
            select(
                Poll.uuid.label("poll_uuid"),
                PollOptions.uuid.label("option_uuid")
            )
            .select_from(Vote)
            .join(Poll, Vote.poll_id == Poll.id)
            .join(PollOptions, Vote.option_id == PollOptions.id)
            .where(Vote.user_id == user_id)
        )
        
        result = await session.execute(stmt)
        return result.fetchall()


vote_crud = VoteCrud()

