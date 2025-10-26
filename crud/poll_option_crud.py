from typing import List, Optional, Any, Union, Coroutine, Sequence

from sqlalchemy import insert, Row, RowMapping
from sqlalchemy.ext.asyncio import AsyncSession

from models import PollOptions

class PollOptionCrud:
    def __init__(self):
        self.table = PollOptions

    async def create_options(self, session: AsyncSession, options: List[dict]) -> Sequence[PollOptions]:
        stmt = insert(PollOptions).values(options).returning(PollOptions)
        result = await session.execute(stmt)
        return result.scalars().all()

poll_option_crud = PollOptionCrud()
