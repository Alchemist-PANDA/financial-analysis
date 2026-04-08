from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
import os
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


def normalize_database_url(url: str) -> str:
    """
    Normalize DB URLs for SQLAlchemy async engines.
    - Enforce `postgresql+asyncpg://` driver.
    - Convert unsupported asyncpg query args:
      `sslmode=require` -> `ssl=require`
      drop `channel_binding`
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if not url.startswith("postgresql+asyncpg://"):
        return url

    parts = urlsplit(url)
    query = dict(parse_qsl(parts.query, keep_blank_values=True))

    sslmode = query.pop("sslmode", None)
    query.pop("channel_binding", None)
    if sslmode and "ssl" not in query:
        query["ssl"] = sslmode

    normalized_query = urlencode(query)
    return urlunsplit((parts.scheme, parts.netloc, parts.path, normalized_query, parts.fragment))

# Database configuration (Dynamic for local vs production)
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    DATABASE_URL = normalize_database_url(DATABASE_URL)
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
