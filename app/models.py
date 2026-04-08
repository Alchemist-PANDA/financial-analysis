from datetime import datetime, timezone
from typing import Optional
from sqlalchemy import String, Float, JSON, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class AnalysisHistory(Base):
    """Stores full institutional analysis results for history and comparison."""
    __tablename__ = "analysis_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), index=True)
    company_name: Mapped[str] = mapped_column(String(255))
    archetype: Mapped[str] = mapped_column(String(50)) # e.g. COMPOUNDER, VALUE TRAP
    
    # Store full analysis as JSON (metrics, flags, diagnosis)
    analysis_data: Mapped[dict] = mapped_column(JSON)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

class Watchlist(Base):
    """User's tracked tickers for the side-by-side comparison mode."""
    __tablename__ = "watchlist"

    id: Mapped[int] = mapped_column(primary_key=True)
    ticker: Mapped[str] = mapped_column(String(20), unique=True)
    company_name: Mapped[str] = mapped_column(String(255))
    added_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )
