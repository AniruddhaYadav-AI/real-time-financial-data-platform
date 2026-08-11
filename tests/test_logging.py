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
