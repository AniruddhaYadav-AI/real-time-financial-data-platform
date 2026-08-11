import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class MarketTrade(Base):
    """
    Represents a raw market trade event.
    """
    __tablename__ = "market_trades"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="RESTRICT"), nullable=False
    )
    exchange_trade_id: Mapped[str] = mapped_column(String, nullable=False)
    price: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    event_time: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    received_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    __table_args__ = (
        UniqueConstraint(
            "instrument_id", "exchange_trade_id", name="uq_trade_instrument_exchange_id"
        ),
        Index("ix_market_trades_instrument_time", "instrument_id", text("event_time DESC")),
    )

class MarketOhlcv(Base):
    """
    Represents a derived OHLCV (Open, High, Low, Close, Volume) candle.
    """
    __tablename__ = "market_ohlcv"

    instrument_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("instruments.id", ondelete="RESTRICT"), primary_key=True
    )
    timeframe: Mapped[str] = mapped_column(String, primary_key=True)
    window_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), primary_key=True)
    open: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    high: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    low: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    close: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
    volume: Mapped[Decimal] = mapped_column(Numeric(20, 8), nullable=False)
