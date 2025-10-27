from sqlalchemy import select, update, insert
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Sequence, Optional
from models import Poll
from models import Like


class LikeCrud:

    def __init__(self):
        self.table = Like
    
    async def create_like(self, session: AsyncSession, user_id: int, poll_id: int, is_active: bool = True) -> Like:
        stmt = insert(Like).values(user_id=user_id, poll_id=poll_id, is_active=is_active).returning(Like)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def toggle_like(self, session: AsyncSession, user_id: int, poll_id: int) -> tuple[bool, Optional[Like]]:
        existing_like = await self.get_like(session, user_id, poll_id)
        
        if existing_like:
            new_is_active = not existing_like.is_active
            stmt = (
                update(Like)
                .where(
                    Like.user_id == user_id,
                    Like.poll_id == poll_id
                )
                .values(is_active=new_is_active)
                .returning(Like)
            )
            result = await session.execute(stmt)
            updated_like = result.scalars().first()
            await session.flush()
            return new_is_active, updated_like
        else:
            new_like = await self.create_like(session, user_id, poll_id, is_active=True)
            await session.flush()
            return True, new_like
    
    async def get_like(self, session: AsyncSession, user_id: int, poll_id: int):
        stmt = select(Like).where(
            Like.user_id == user_id,
            Like.poll_id == poll_id
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_active_like(self, session: AsyncSession, user_id: int, poll_id: int):
        stmt = select(Like).where(
            Like.user_id == user_id,
            Like.poll_id == poll_id,
            Like.is_active == True
        )
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_likes_by_poll(self, session: AsyncSession, poll_id: int) -> Sequence[Like]:
        stmt = select(Like).where(Like.poll_id == poll_id, Like.is_active == True)
        result = await session.execute(stmt)
        return result.scalars().all()
    
    async def count_likes_by_poll(self, session: AsyncSession, poll_id: int) -> int:
        stmt = select(Like).where(Like.poll_id == poll_id, Like.is_active == True)
        result = await session.execute(stmt)
        return len(result.scalars().all())
    
    async def get_liked_polls_by_user(self, session: AsyncSession, user_id: int):
        stmt = select(Poll.uuid).join(
            Like, Poll.id == Like.poll_id
        ).where(
            Like.user_id == user_id,
            Like.is_active == True
        )
        result = await session.execute(stmt)
        return [row[0] for row in result.fetchall()]


like_crud = LikeCrud()
