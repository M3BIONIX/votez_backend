from typing import Sequence, Optional
from uuid import UUID
from sqlalchemy import insert, update, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager
from models import Poll, PollOptions


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
        """Get all active polls with their active options loaded"""
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


poll_crud = PollCrud()