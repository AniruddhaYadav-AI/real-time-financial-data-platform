"""Unit tests for event schemas."""

from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from financial_platform.events.schemas import DLQEnvelope, RawTradeEvent


def test_raw_trade_event_valid() -> None:
    """Valid construction works correctly."""
    inst_id = uuid4()
    now_utc = datetime.now(UTC)
    event = RawTradeEvent(
        instrument_id=inst_id,
        exchange_trade_id="EXT-123",
        price=Decimal("150.25"),
        volume=Decimal("100.5"),
        event_time=now_utc,
    )
    assert event.instrument_id == inst_id
    assert event.exchange_trade_id == "EXT-123"
    assert event.price == Decimal("150.25")
    assert event.volume == Decimal("100.5")
    assert event.event_time == now_utc


def test_raw_trade_event_negative_price_rejection() -> None:
    with pytest.raises(ValidationError) as exc:
        RawTradeEvent(
            instrument_id=uuid4(),
            exchange_trade_id="EXT-1",
            price=Decimal("-10.0"),
            volume=Decimal("100.0"),
            event_time=datetime.now(UTC),
        )
    assert "Input should be greater than 0" in str(exc.value)


def test_raw_trade_event_zero_price_rejection() -> None:
    with pytest.raises(ValidationError) as exc:
        RawTradeEvent(
            instrument_id=uuid4(),
            exchange_trade_id="EXT-1",
            price=Decimal("0"),
            volume=Decimal("100.0"),
            event_time=datetime.now(UTC),
        )
    assert "Input should be greater than 0" in str(exc.value)


def test_raw_trade_event_negative_volume_rejection() -> None:
    with pytest.raises(ValidationError) as exc:
        RawTradeEvent(
            instrument_id=uuid4(),
            exchange_trade_id="EXT-1",
            price=Decimal("10.0"),
            volume=Decimal("-100.0"),
            event_time=datetime.now(UTC),
        )
    assert "Input should be greater than 0" in str(exc.value)


def test_raw_trade_event_zero_volume_rejection() -> None:
    with pytest.raises(ValidationError) as exc:
        RawTradeEvent(
            instrument_id=uuid4(),
            exchange_trade_id="EXT-1",
            price=Decimal("10.0"),
            volume=Decimal("0.0"),
            event_time=datetime.now(UTC),
        )
    assert "Input should be greater than 0" in str(exc.value)


def test_raw_trade_event_max_digits_enforcement() -> None:
    with pytest.raises(ValidationError) as exc:
        RawTradeEvent(
            instrument_id=uuid4(),
            exchange_trade_id="EXT-1",
            price=Decimal("123456789012345678901.0"),  # 21 digits
            volume=Decimal("100.0"),
            event_time=datetime.now(UTC),
        )
    assert "max_digits" in str(exc.value)


def test_raw_trade_event_decimal_places_enforcement() -> None:
    with pytest.raises(ValidationError) as exc:
        RawTradeEvent(
            instrument_id=uuid4(),
            exchange_trade_id="EXT-1",
            price=Decimal("10.123456789"),  # 9 decimal places
            volume=Decimal("100.0"),
            event_time=datetime.now(UTC),
        )
    assert "decimal places" in str(exc.value)


def test_raw_trade_event_naive_datetime_rejection() -> None:
    with pytest.raises(ValidationError) as exc:
        RawTradeEvent(
            instrument_id=uuid4(),
            exchange_trade_id="EXT-1",
            price=Decimal("10.0"),
            volume=Decimal("100.0"),
            event_time=datetime.now(),  # naive
        )
    assert "timezone info" in str(exc.value)


def test_raw_trade_event_non_utc_datetime_normalization() -> None:
    non_utc_tz = timezone(timedelta(hours=5))
    non_utc_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=non_utc_tz)

    event = RawTradeEvent(
        instrument_id=uuid4(),
        exchange_trade_id="EXT-1",
        price=Decimal("10.0"),
        volume=Decimal("100.0"),
        event_time=non_utc_dt,
    )

    assert event.event_time.tzinfo == UTC
    assert event.event_time == non_utc_dt.astimezone(UTC)


def test_raw_trade_event_event_id_default() -> None:
    event = RawTradeEvent(
        instrument_id=uuid4(),
        exchange_trade_id="EXT-1",
        price=Decimal("10.0"),
        volume=Decimal("100.0"),
        event_time=datetime.now(UTC),
    )
    assert event.event_id is not None


def test_raw_trade_event_ingested_at_default() -> None:
    event = RawTradeEvent(
        instrument_id=uuid4(),
        exchange_trade_id="EXT-1",
        price=Decimal("10.0"),
        volume=Decimal("100.0"),
        event_time=datetime.now(UTC),
    )
    assert event.ingested_at is not None
    assert event.ingested_at.tzinfo == UTC


def test_raw_trade_event_schema_version_default() -> None:
    event = RawTradeEvent(
        instrument_id=uuid4(),
        exchange_trade_id="EXT-1",
        price=Decimal("10.0"),
        volume=Decimal("100.0"),
        event_time=datetime.now(UTC),
    )
    assert event.schema_version == 1


def test_raw_trade_event_schema_version_minimum_rejection() -> None:
    with pytest.raises(ValidationError) as exc:
        RawTradeEvent(
            instrument_id=uuid4(),
            exchange_trade_id="EXT-1",
            price=Decimal("10.0"),
            volume=Decimal("100.0"),
            event_time=datetime.now(UTC),
            schema_version=0,
        )
    assert "greater than or equal to 1" in str(exc.value)


def test_raw_trade_event_unknown_field_ignoring() -> None:
    data = {
        "instrument_id": uuid4(),
        "exchange_trade_id": "EXT-1",
        "price": Decimal("10.0"),
        "volume": Decimal("100.0"),
        "event_time": datetime.now(UTC),
        "unknown_future_field": "should be ignored",
    }
    event = RawTradeEvent.model_validate(data)
    assert not hasattr(event, "unknown_future_field")


def test_dlq_envelope_valid() -> None:
    event_id = uuid4()
    now_utc = datetime.now(UTC)
    envelope = DLQEnvelope(
        event_id=event_id,
        original_payload='{"bad": "data"}',
        error_reason="validation_error",
        error_details="pydantic error details",
        topic="trades",
        partition=0,
        offset=123,
        failed_at=now_utc,
    )
    assert envelope.event_id == event_id
    assert envelope.original_payload == '{"bad": "data"}'
    assert envelope.error_reason == "validation_error"
    assert envelope.error_details == "pydantic error details"
    assert envelope.topic == "trades"
    assert envelope.partition == 0
    assert envelope.offset == 123
    assert envelope.failed_at == now_utc


def test_dlq_envelope_optional_fields() -> None:
    envelope = DLQEnvelope(
        original_payload="raw_bytes",
        error_reason="deserialization_error",
        topic="trades",
        partition=0,
        offset=124,
    )
    assert envelope.event_id is None
    assert envelope.error_details is None


def test_dlq_envelope_failed_at_default() -> None:
    envelope = DLQEnvelope(
        original_payload="raw_bytes",
        error_reason="error",
        topic="trades",
        partition=0,
        offset=1,
    )
    assert envelope.failed_at is not None
    assert envelope.failed_at.tzinfo == UTC


def test_dlq_envelope_non_utc_failed_at_normalization() -> None:
    non_utc_tz = timezone(timedelta(hours=5))
    non_utc_dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=non_utc_tz)

    envelope = DLQEnvelope(
        original_payload="raw_bytes",
        error_reason="error",
        topic="trades",
        partition=0,
        offset=1,
        failed_at=non_utc_dt,
    )
    assert envelope.failed_at.tzinfo == UTC
    assert envelope.failed_at == non_utc_dt.astimezone(UTC)
