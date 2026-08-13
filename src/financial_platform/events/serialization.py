"""Serialization and deserialization logic for Kafka events."""

from financial_platform.events.schemas import RawTradeEvent


def serialize_event(event: RawTradeEvent) -> bytes:
    """Serialize a RawTradeEvent to a UTF-8 JSON byte payload.

    Decimals are serialized as JSON strings.
    Datetimes are serialized as ISO-8601 strings.
    UUIDs are serialized as canonical hyphenated strings.
    """
    return event.model_dump_json().encode("utf-8")


def deserialize_event(payload: bytes) -> RawTradeEvent:
    """Deserialize a UTF-8 JSON byte payload into a RawTradeEvent.

    Raises:
        pydantic.ValidationError: If schema constraints are violated.
        ValueError: If JSON is malformed.
    """
    return RawTradeEvent.model_validate_json(payload)
