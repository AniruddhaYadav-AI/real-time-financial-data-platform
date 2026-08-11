import uuid

from sqlalchemy import Boolean, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from .base import Base


class Instrument(Base):
    """
    Represents a financial instrument specific to a source venue.
    """
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    venue: Mapped[str] = mapped_column(String, nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    asset_class: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    __table_args__ = (
        UniqueConstraint('venue', 'symbol', name='uq_instrument_venue_symbol'),
    )
