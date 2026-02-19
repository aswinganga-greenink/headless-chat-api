from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from src.core.config import get_settings
import logging

settings = get_settings()
logger = logging.getLogger(__name__)

# Create the Async Engine
# echo=True will log all SQL queries, useful for debugging but should be False in prod
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    future=True,
    connect_args={"ssl": False}
)

# Create the session factory
# exclude_pending=True ensures we only return committed data by default
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)

async def get_db() -> AsyncSession:
    """
    Dependency injection for database sessions.
    
    Yields:
        AsyncSession: An asynchronous database session.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()
