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
    
    async def add_options_to_poll(self, session: AsyncSession, poll_id: int, options: List[dict]) -> Sequence[PollOptions]:
        """Add new options to an existing poll."""
        # Add poll_id to each option
        options_data = [{**opt, "poll_id": poll_id} for opt in options]
        return await self.create_options(session, options_data)
    
    async def soft_delete_options_by_uuids(self, session: AsyncSession, option_uuids: List[str]) -> int:
        """Soft delete specific options by their UUIDs by setting is_active to False."""
        from uuid import UUID
        
        # Convert UUID strings to UUID objects
        uuid_objects = [UUID(uuid_str) for uuid_str in option_uuids]
        
        stmt = (
            update(PollOptions)
            .where(PollOptions.uuid.in_(uuid_objects))
            .values(is_active=False)
        )
        result = await session.execute(stmt)
        return result.rowcount
    
    async def get_option_by_uuid(self, session: AsyncSession, option_uuid: str) -> PollOptions:
        """Get an option by its UUID."""
        from uuid import UUID
        
        uuid_obj = UUID(option_uuid)
        stmt = select(PollOptions).where(PollOptions.uuid == uuid_obj)
        result = await session.execute(stmt)
        return result.scalars().first()


poll_option_crud = PollOptionCrud()
