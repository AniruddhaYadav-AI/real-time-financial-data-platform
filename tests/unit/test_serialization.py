"""Unit tests for event serialization."""

import json
from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

import pytest
from pydantic import ValidationError

from financial_platform.events.schemas import RawTradeEvent
from financial_platform.events.serialization import deserialize_event, serialize_event


def test_serialization_successful_round_trip() -> None:
    original = RawTradeEvent(
        event_id=uuid4(),
        instrument_id=uuid4(),
        exchange_trade_id="EXT-1",
        price=Decimal("150.25"),
        volume=Decimal("100.5"),
        event_time=datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC),
        ingested_at=datetime(2025, 1, 1, 12, 0, 1, tzinfo=UTC),
        schema_version=1,
    )

    payload = serialize_event(original)
    assert isinstance(payload, bytes)

    deserialized = deserialize_event(payload)
    assert deserialized == original


def test_serialization_decimal_as_json_strings() -> None:
    event = RawTradeEvent(
        instrument_id=uuid4(),
        exchange_trade_id="EXT-1",
        price=Decimal("150.25"),
        volume=Decimal("100.5"),
        event_time=datetime.now(UTC),
    )
    payload = serialize_event(event)
    data = json.loads(payload.decode("utf-8"))

    assert data["price"] == "150.25"
    assert data["volume"] == "100.5"


def test_serialization_uuid_as_canonical_strings() -> None:
    inst_id = uuid4()
    event = RawTradeEvent(
        instrument_id=inst_id,
        exchange_trade_id="EXT-1",
        price=Decimal("10.0"),
        volume=Decimal("10.0"),
        event_time=datetime.now(UTC),
    )
    payload = serialize_event(event)
    data = json.loads(payload.decode("utf-8"))

    assert data["instrument_id"] == str(inst_id)


def test_serialization_datetime_as_iso8601_utc() -> None:
    dt = datetime(2025, 1, 1, 12, 0, 0, tzinfo=UTC)
    event = RawTradeEvent(
        instrument_id=uuid4(),
        exchange_trade_id="EXT-1",
        price=Decimal("10.0"),
        volume=Decimal("10.0"),
        event_time=dt,
    )
    payload = serialize_event(event)
    data = json.loads(payload.decode("utf-8"))

    assert data["event_time"] == "2025-01-01T12:00:00Z"


def test_deserialization_malformed_json_rejection() -> None:
    with pytest.raises(ValidationError):
        deserialize_event(b"{malformed_json: true")


def test_deserialization_missing_required_field_rejection() -> None:
    data = {
        "instrument_id": str(uuid4()),
        "price": "10.0",
        "volume": "10.0",
        "event_time": "2025-01-01T12:00:00Z",
    }
    # missing exchange_trade_id
    with pytest.raises(ValidationError) as exc:
        deserialize_event(json.dumps(data).encode("utf-8"))
    assert "exchange_trade_id" in str(exc.value)


def test_deserialization_json_numeric_price_volume_rejection() -> None:
    data = {
        "event_id": str(uuid4()),
        "instrument_id": str(uuid4()),
        "exchange_trade_id": "EXT-1",
        "price": 150.25,  # float, should be rejected
        "volume": 100.5,  # float, should be rejected
        "event_time": "2025-01-01T12:00:00Z",
        "ingested_at": "2025-01-01T12:00:01Z",
        "schema_version": 1,
    }
    with pytest.raises(ValidationError) as exc:
        deserialize_event(json.dumps(data).encode("utf-8"))
    assert "Financial fields must be provided as JSON strings" in str(exc.value)


def test_deserialization_unknown_field_compatibility() -> None:
    data = {
        "event_id": str(uuid4()),
        "instrument_id": str(uuid4()),
        "exchange_trade_id": "EXT-1",
        "price": "150.25",
        "volume": "100.5",
        "event_time": "2025-01-01T12:00:00Z",
        "ingested_at": "2025-01-01T12:00:01Z",
        "schema_version": 1,
        "unknown_future_field": "some_value",
    }
    event = deserialize_event(json.dumps(data).encode("utf-8"))
    assert not hasattr(event, "unknown_future_field")
    assert event.price == Decimal("150.25")


def test_deserialization_json_integer_price_volume_rejection() -> None:
    data = {
        "event_id": str(uuid4()),
        "instrument_id": str(uuid4()),
        "exchange_trade_id": "EXT-1",
        "price": 150,  # integer, should be rejected
        "volume": 100,  # integer, should be rejected
        "event_time": "2025-01-01T12:00:00Z",
        "ingested_at": "2025-01-01T12:00:01Z",
        "schema_version": 1,
    }
    with pytest.raises(ValidationError) as exc:
        deserialize_event(json.dumps(data).encode("utf-8"))
    assert "Financial fields must be provided as JSON strings" in str(exc.value)
