from sqlalchemy import insert
from sqlalchemy.ext.asyncio import AsyncSession
from models import Poll

class PollCrud:
    def __init__(self):
        self.table = Poll

    async def create_poll(self, session: AsyncSession, poll_data: dict) -> Poll:
        stmt = insert(Poll).values(**poll_data).returning(Poll)
        result = await session.execute(stmt)
        return result.scalars().first()


poll_crud = PollCrud()