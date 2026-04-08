# from sqlalchemy import create_url (Removed to fix ImportError, not used)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os

# Database configuration (Dynamic for local vs production)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # If using PostgreSQL (e.g. Neon), ensure the protocol is correct for SQLAlchemy async
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql+asyncpg://", 1)
else:
    # Default to local SQLite
    DB_FILE = "financial_agent.db"
    DATABASE_URL = f"sqlite+aiosqlite:///{DB_FILE}"

# Create async engine
engine = create_async_engine(DATABASE_URL, echo=False)

# Create session factory
async_session = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

class Base(DeclarativeBase):
    pass

async def get_db():
    """Dependency for getting async database session."""
    async with async_session() as session:
        yield session

async def init_db():
    """Initialize database tables."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
