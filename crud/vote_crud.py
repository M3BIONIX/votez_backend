from sqlalchemy import select, delete, insert, func
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence
from models import Vote
from models import Poll, PollOptions
from sqlalchemy.orm import selectinload
from schemas.user_schema import VotedPollInfo


class VoteCrud:

    def __init__(self):
        self.table = Vote
    
    async def create_vote(self, session: AsyncSession, user_id: int, poll_id: int, option_id: int) -> Vote:
        stmt = insert(Vote).values(
            user_id=user_id,
            poll_id=poll_id,
            option_id=option_id
        ).returning(Vote)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def delete_vote(self, session: AsyncSession, user_id: int, poll_id: int) -> bool:
        stmt = delete(Vote).where(
            Vote.user_id == user_id,
            Vote.poll_id == poll_id
        )
        result = await session.execute(stmt)
        return result.rowcount > 0
    
    async def get_vote(self, session: AsyncSession, user_id: int, poll_id: int):
        stmt = select(Vote).where(
            Vote.user_id == user_id,
            Vote.poll_id == poll_id
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_votes_by_poll(self, session: AsyncSession, poll_id: int) -> Sequence[Vote]:
        stmt = select(Vote).where(Vote.poll_id == poll_id)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def get_vote_counts_by_poll(self, session: AsyncSession, poll_id: int) -> dict:
        stmt = select(
            Vote.option_id,
            func.count(Vote.option_id).label("count")
        ).where(
            Vote.poll_id == poll_id
        ).group_by(Vote.option_id)
        
        result = await session.execute(stmt)
        return {row.option_id: row.count for row in result}
    
    async def get_votes_by_user(self, session: AsyncSession, user_id: int):
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
    
    async def get_voted_polls_info(self, session: AsyncSession, user_id: int):
        votes = await self.get_votes_by_user(session, user_id)
        
        voted_polls = []
        for vote_row in votes:
            poll_result = await session.execute(
                select(Poll)
                .options(selectinload(Poll.poll_options))
                .where(Poll.uuid == vote_row.poll_uuid)
            )
            poll = poll_result.scalars().first()
            
            if poll:
                option_exists_result = await session.execute(
                    select(PollOptions)
                    .where(PollOptions.uuid == vote_row.option_uuid)
                    .where(PollOptions.is_active == True)
                )
                voted_option = option_exists_result.scalars().first()
                
                if not voted_option:
                    continue
                
                vote_counts = await self.get_vote_counts_by_poll(session, poll.id)
                total_votes = sum(vote_counts.values())
                
                options_result = await session.execute(
                    select(PollOptions)
                    .where(PollOptions.poll_id == poll.id)
                    .where(PollOptions.is_active == True)
                )
                poll_options = options_result.scalars().all()
                
                option_percentages = {}
                if total_votes > 0:
                    for opt in poll_options:
                        option_vote_count = vote_counts.get(opt.id, 0)
                        percentage = (option_vote_count / total_votes) * 100
                        option_percentages[str(opt.uuid)] = round(percentage, 2)
                else:
                    for opt in poll_options:
                        option_percentages[str(opt.uuid)] = 0.0
                
                voted_polls.append(
                    VotedPollInfo(
                        poll_uuid=vote_row.poll_uuid,
                        option_uuid=vote_row.option_uuid,
                        total_votes=total_votes,
                        summary=option_percentages
                    )
                )
        
        return voted_polls
    
    async def get_vote_percentages(
        self, 
        session: AsyncSession, 
        poll_id: int,
        poll_options: Sequence
    ) -> tuple[int, dict[str, float]]:
        vote_counts = await self.get_vote_counts_by_poll(session, poll_id)
        total_votes = sum(vote_counts.values())
        
        option_percentages = {}
        if total_votes > 0:
            for opt in poll_options:
                option_vote_count = vote_counts.get(opt.id, 0)
                percentage = (option_vote_count / total_votes) * 100
                option_percentages[str(opt.uuid)] = round(percentage, 2)
        else:
            for opt in poll_options:
                option_percentages[str(opt.uuid)] = 0.0
        
        return total_votes, option_percentages
    
    async def upsert_vote(
        self,
        session: AsyncSession,
        user_id: int,
        poll_id: int,
        option_id: int
    ) -> Vote:
        await self.delete_vote(session, user_id, poll_id)
        return await self.create_vote(session, user_id, poll_id, option_id)


vote_crud = VoteCrud()

