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
        dollar_count = 0
        
        for line in sql.split('\n'):
            # Skip pure comment lines
            stripped = line.strip()
            if stripped.startswith('--') and not current_statement:
                continue
            
            # Count dollar signs to track quote state
            if '$$' in line:
                dollar_count += line.count('$$')
                in_dollar_quote = (dollar_count % 2) == 1
            
            # Add line to current statement
            if stripped:  # Only add non-empty lines
                current_statement.append(line)
            
            # Check if this line ends a statement (semicolon outside dollar quotes)
            if ';' in line and not in_dollar_quote:
                stmt = '\n'.join(current_statement).strip()
                if stmt:
                    statements.append(stmt)
                current_statement = []
        
        # Execute each statement in order
        logger.info(f"Executing {len(statements)} SQL statements...")
        for idx, statement in enumerate(statements, 1):
            try:
                await conn.execute(text(statement))
                logger.debug(f"Statement {idx}/{len(statements)} executed successfully")
            except Exception as e:
                logger.error(f"Failed to execute statement {idx}: {str(e)[:100]}")
                raise
    
    logger.info("Database initialized successfully")


async def close_db() -> None:
    """Close database connections."""
    await engine.dispose()
    logger.info("Database connections closed")
