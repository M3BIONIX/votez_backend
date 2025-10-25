from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core.settings import settings

async_engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URI,
    pool_pre_ping=True,
    pool_size=settings.POSTGRES_POOL_SIZE,
    max_overflow=settings.POSTGRES_MAX_OVERFLOW,
    pool_recycle=600,
    pool_use_lifo=True,
)
AsyncSessionLocal = async_sessionmaker(async_engine, autocommit=False, expire_on_commit=False)
