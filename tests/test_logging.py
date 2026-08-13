"""Unit tests for the JSONFormatter structured logging implementation."""

import json
import logging

from financial_platform.core.logging import JSONFormatter


def test_json_formatter_output() -> None:
    """Test that JSONFormatter formats log record into valid JSON with expected keys."""
    formatter = JSONFormatter(app_env="test")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=10,
        msg="Test log message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    assert data["message"] == "Test log message"
    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["environment"] == "test"
    assert "timestamp" in data


def test_json_formatter_extra_fields_included() -> None:
    """Extra fields supplied via extra={...} are merged into the JSON output."""
    formatter = JSONFormatter(app_env="test")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=20,
        msg="Event published",
        args=(),
        exc_info=None,
    )
    # Simulate logger.info("msg", extra={"event_id": ..., "instrument_id": ...})
    record.event_id = "evt-abc-123"
    record.instrument_id = "inst-def-456"
    record.topic = "market.trades.raw"

    formatted = formatter.format(record)
    data = json.loads(formatted)

    # Extra fields present
    assert data["event_id"] == "evt-abc-123"
    assert data["instrument_id"] == "inst-def-456"
    assert data["topic"] == "market.trades.raw"

    # Standard fields still present and unchanged
    assert data["message"] == "Event published"
    assert data["level"] == "INFO"
    assert data["logger"] == "test_logger"
    assert data["environment"] == "test"
    assert "timestamp" in data


def test_json_formatter_standard_fields_not_duplicated() -> None:
    """Standard LogRecord attributes (levelname, lineno, etc.) are not duplicated
    as extra fields in the output — they appear only under their mapped names."""
    formatter = JSONFormatter(app_env="test")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.WARNING,
        pathname="test.py",
        lineno=30,
        msg="Warning message",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    # Standard LogRecord internals must NOT appear as raw extra fields
    assert "levelno" not in data    # raw int level — mapped as "level" (str)
    assert "lineno" not in data     # source line number — not surfaced
    assert "pathname" not in data   # full file path — not surfaced
    assert "created" not in data    # epoch timestamp — mapped as "timestamp"


def test_json_formatter_no_extra_fields_unaffected() -> None:
    """When no extra fields are supplied the output is identical to baseline behavior."""
    formatter = JSONFormatter(app_env="production")
    record = logging.LogRecord(
        name="my_logger",
        level=logging.ERROR,
        pathname="app.py",
        lineno=99,
        msg="Something went wrong",
        args=(),
        exc_info=None,
    )
    formatted = formatter.format(record)
    data = json.loads(formatted)

    # Exactly the five standard keys — nothing extra
    assert set(data.keys()) == {"timestamp", "level", "logger", "message", "environment"}
    assert data["environment"] == "production"
    assert data["level"] == "ERROR"


def test_json_formatter_reserved_fields_protected() -> None:
    """Extra fields cannot overwrite the formatter's reserved output fields."""
    formatter = JSONFormatter(app_env="test")
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=40,
        msg="Authoritative message",
        args=(),
        exc_info=None,
    )
    # Attempt to overwrite reserved fields via extra
    record.message = "Malicious extra message"
    record.level = "CRITICAL"
    record.environment = "production"

    formatted = formatter.format(record)
    data = json.loads(formatted)

    # Original authoritative values must remain
    assert data["message"] == "Authoritative message"
    assert data["level"] == "INFO"
    assert data["environment"] == "test"
    assert data["logger"] == "test_logger"
