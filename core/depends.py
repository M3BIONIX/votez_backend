from typing import Annotated, AsyncGenerator, Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from jose import jwt, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from starlette import status
from typing_extensions import TypeAlias

from core.async_engine import AsyncSessionLocal
from core.auth import bearer_scheme
from core.settings import settings
from models import UserModel


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

AsyncDBSession: TypeAlias = Annotated[AsyncSession, Depends(get_session)]


async def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)]
) -> UserModel:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    # Check if credentials were provided
    if credentials is None:
        raise credentials_exception

    try:
        # Extract token from Bearer credentials
        token = credentials.credentials
        if not token or token.strip() == "":
            raise credentials_exception
        
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_uuid: str = payload.get("sub")
        if user_uuid is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    async with AsyncSessionLocal() as session:
        # Look up user by UUID instead of ID for better security
        stmt = select(UserModel).where(UserModel.uuid == user_uuid)
        result = await session.execute(stmt)
        user = result.scalars().first()

        if user is None:
            raise credentials_exception

        return user

AuthenticatedUser: TypeAlias = Annotated[UserModel, Depends(get_current_user)]
