from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from .config import db_settings

engine = create_async_engine(
    db_settings.database_url,
    pool_pre_ping=True,
    # reasonable defaults for connection pooling
    pool_size=5,
    max_overflow=10,
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting an async database session."""
    async with async_session_maker() as session:
        yield session
