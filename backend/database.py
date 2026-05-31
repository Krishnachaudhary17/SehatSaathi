"""
database.py — Async SQLAlchemy engine + session factory
"""

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv
import os

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

# Create the async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# Base class for all ORM models
class Base(DeclarativeBase):
    pass


# Dependency to get a DB session in route handlers
async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
