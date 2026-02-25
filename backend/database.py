import os
from typing import AsyncGenerator
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

# Load environment variables
load_dotenv()

# Get database URL from environment
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=False,  # Set to True for SQL query logging in development
    future=True,
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)

# Create declarative base
class Base(DeclarativeBase):
    """Base class for all database models"""
    pass


# Dependency function for FastAPI
async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session for each request.
    Automatically handles session lifecycle and cleanup.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
