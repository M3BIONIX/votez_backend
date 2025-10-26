from typing import List, Sequence

from sqlalchemy import insert, delete, update, select
from sqlalchemy.ext.asyncio import AsyncSession

from models import PollOptions

class PollOptionCrud:
    def __init__(self):
        self.table = PollOptions

    async def create_options(self, session: AsyncSession, options: List[dict]) -> Sequence[PollOptions]:
        stmt = insert(PollOptions).values(options).returning(PollOptions)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def get_options_by_poll_id(self, session: AsyncSession, poll_id: int) -> Sequence[PollOptions]:
        stmt = select(PollOptions).where(PollOptions.poll_id == poll_id, PollOptions.is_active == True)
        result = await session.execute(stmt)
        return result.scalars().all()

    async def update_option_by_id(self, session: AsyncSession, option_id: int, option_data: dict) -> PollOptions:
        stmt = update(PollOptions).where(PollOptions.id == option_id).values(**option_data).returning(PollOptions)
        result = await session.execute(stmt)
        return result.scalars().first()

    async def delete_option_by_id(self, session: AsyncSession, option_id: int) -> None:
        stmt = delete(PollOptions).where(PollOptions.id == option_id)
        await session.execute(stmt)

    async def delete_options_by_poll_id(self, session: AsyncSession, poll_id: int) -> None:
        """Delete all options for a specific poll"""
        stmt = delete(PollOptions).where(PollOptions.poll_id == poll_id)
        await session.execute(stmt)

    async def soft_delete_options_by_poll_id(self, session: AsyncSession, poll_id: int) -> None:
        """Soft delete all options for a specific poll by setting is_active to False"""
        stmt = update(PollOptions).where(PollOptions.poll_id == poll_id).values(is_active=False)
        await session.execute(stmt)


poll_option_crud = PollOptionCrud()
