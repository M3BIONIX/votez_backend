from typing import Annotated, AsyncGenerator
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing_extensions import TypeAlias

from core.async_engine import AsyncSessionLocal


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

AsyncDBSession: TypeAlias = Annotated[AsyncSession, Depends(get_session)]
