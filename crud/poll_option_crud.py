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
    
    async def get_active_option_by_uuid_and_poll_id(
        self, 
        session: AsyncSession, 
        option_uuid: str, 
        poll_id: int
    ) -> PollOptions:
        """Get an active option by its UUID that belongs to a specific poll."""
        from uuid import UUID
        
        uuid_obj = UUID(option_uuid)
        stmt = (
            select(PollOptions)
            .where(PollOptions.uuid == uuid_obj)
            .where(PollOptions.poll_id == poll_id)
            .where(PollOptions.is_active == True)
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_active_options_by_poll_id(self, session: AsyncSession, poll_id: int) -> Sequence[PollOptions]:
        stmt = (
            select(PollOptions)
            .where(PollOptions.poll_id == poll_id)
            .where(PollOptions.is_active == True)
        )
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def validate_option_uuids_belong_to_poll(
        self, 
        session: AsyncSession, 
        poll_id: int, 
        option_uuids: List[str]
    ) -> bool:
        active_options = await self.get_active_options_by_poll_id(session, poll_id)
        valid_option_uuids = [str(opt.uuid) for opt in active_options]
        requested_uuids = [str(uuid) for uuid in option_uuids]
        
        return set(requested_uuids).issubset(set(valid_option_uuids))
    
    async def soft_delete_options_by_uuids_for_poll(
        self, 
        session: AsyncSession, 
        poll_id: int, 
        option_uuids: List[str]
    ) -> int:
        active_options = await self.get_active_options_by_poll_id(session, poll_id)
        valid_option_uuids = [str(opt.uuid) for opt in active_options]
        requested_uuids = [str(uuid) for uuid in option_uuids]
        
        valid_requested_uuids = [uuid for uuid in requested_uuids if uuid in valid_option_uuids]
        
        if not valid_requested_uuids:
            return 0
        
        return await self.soft_delete_options_by_uuids(session, valid_requested_uuids)


poll_option_crud = PollOptionCrud()
