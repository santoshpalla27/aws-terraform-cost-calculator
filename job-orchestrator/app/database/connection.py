"""
PostgreSQL database connection.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)

# Create async engine
engine = create_async_engine(
    settings.database_url,
    echo=False,
    pool_pre_ping=True,
    pool_size=10,
    max_overflow=20
)

# Create session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for models
Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Get database session.
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Initialize database (run migrations)."""
    logger.info("Initializing database...")
    
    # In production, use Alembic for migrations
    # For now, we'll execute the SQL file directly
    async with engine.begin() as conn:
        # Read and execute migration SQL
        with open("app/database/migrations/001_initial.sql", "r") as f:
            sql = f.read()
            # Split by semicolon and execute each statement
            for statement in sql.split(';'):
                if statement.strip():
                    await conn.execute(statement)
    
    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
