from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from models.user_model import UserModel
from core.auth import get_password_hash


class UserCrud:

    def __init__(self):
        self.table = UserModel
    
    async def create_user(self, session: AsyncSession, user_data: dict) -> UserModel:
        user_data["hashed_password"] = get_password_hash(user_data.pop("password"))
        user = UserModel(**user_data)
        session.add(user)
        await session.flush()
        await session.refresh(user)
        return user
    
    async def get_user_by_email(self, session: AsyncSession, email: str) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.email == email)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_user_by_id(self, session: AsyncSession, user_id: int) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.id == user_id)
        result = await session.execute(stmt)
        return result.scalars().first()
    
    async def get_user_by_uuid(self, session: AsyncSession, user_uuid) -> Optional[UserModel]:
        stmt = select(UserModel).where(UserModel.uuid == user_uuid)
        result = await session.execute(stmt)
        return result.scalars().first()


user_crud = UserCrud()

