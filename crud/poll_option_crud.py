from typing import List, Sequence, Dict

from sqlalchemy import insert, delete, update, select, case
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

    async def update_option_by_id(self, session: AsyncSession, option_ids: List[int], id_to_title_map: Dict[int, str]) -> Sequence[PollOptions]:
        case_stmt = case(
            *[(PollOptions.id == opt_id, title) for opt_id, title in id_to_title_map.items()],
            else_=PollOptions.option_name
        )
        
        stmt = (
            update(PollOptions)
            .where(PollOptions.id.in_(option_ids))
            .values(option_name=case_stmt,
                    version_id = PollOptions.version_id+1)
            .returning(PollOptions)
        )
        
        result = await session.execute(stmt)
        return result.scalars().all()


    async def soft_delete_options_by_poll_id(self, session: AsyncSession, poll_id: int) -> None:
        """Soft delete all options for a specific poll by setting is_active to False"""
        stmt = update(PollOptions).where(PollOptions.poll_id == poll_id).values(is_active=False)
        await session.execute(stmt)


poll_option_crud = PollOptionCrud()
