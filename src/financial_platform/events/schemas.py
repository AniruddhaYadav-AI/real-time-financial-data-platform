"""Event schemas and validation contracts for the financial data platform."""

from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator


class RawTradeEvent(BaseModel):
    """Raw trade event representing a single market execution."""

    model_config = ConfigDict(extra="ignore")

    event_id: UUID = Field(default_factory=uuid4)
    instrument_id: UUID
    exchange_trade_id: str
    price: Decimal = Field(gt=0, max_digits=20, decimal_places=8)
    volume: Decimal = Field(gt=0, max_digits=20, decimal_places=8)
    event_time: AwareDatetime
    ingested_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))
    schema_version: int = Field(default=1, ge=1)

    @field_validator("price", "volume", mode="before")
    @classmethod
    def require_string_for_decimal(cls, v: Any) -> Any:
        """Enforce strict string inputs for Decimal fields to prevent precision loss."""
        if isinstance(v, Decimal):
            return v
        if not isinstance(v, str):
            raise ValueError("Financial fields must be provided as JSON strings")
        return v

    @field_validator("event_time", "ingested_at", mode="after")
    @classmethod
    def normalize_to_utc(cls, v: datetime) -> datetime:
        """Ensure datetimes are explicitly normalized to UTC."""
        return v.astimezone(UTC)


class DLQEnvelope(BaseModel):
    """Dead Letter Queue envelope wrapping failed payloads."""

    model_config = ConfigDict(extra="ignore")

    event_id: UUID | None = None
    original_payload: str
    error_reason: str
    error_details: str | None = None
    topic: str
    partition: int
    offset: int
    failed_at: AwareDatetime = Field(default_factory=lambda: datetime.now(UTC))

    @field_validator("failed_at", mode="after")
    @classmethod
    def normalize_to_utc(cls, v: datetime) -> datetime:
        """Ensure failed_at is explicitly normalized to UTC."""
        return v.astimezone(UTC)
