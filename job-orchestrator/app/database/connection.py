"""
PostgreSQL database connection.
"""
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from sqlalchemy import text
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
        # Read migration SQL
        with open("app/database/migrations/001_initial.sql", "r") as f:
            sql = f.read()
        
        # Smart split: handle dollar-quoted strings in PostgreSQL functions
        statements = []
        current_statement = []
        in_dollar_quote = False
        
        for line in sql.split('\n'):
            # Check for dollar-quote delimiters
            if '$$' in line:
                in_dollar_quote = not in_dollar_quote
            
            current_statement.append(line)
            
            # If we hit a semicolon outside of dollar quotes, it's a statement boundary
            if ';' in line and not in_dollar_quote:
                stmt = '\n'.join(current_statement).strip()
                if stmt and not stmt.startswith('--'):
                    statements.append(stmt)
                current_statement = []
        
        # Execute each statement
        for statement in statements:
            if statement.strip():
                await conn.execute(text(statement))
    
    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
