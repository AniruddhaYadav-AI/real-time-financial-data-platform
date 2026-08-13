import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

# Comprehensive set of standard LogRecord attributes populated by Python's
# logging framework.  Any key in record.__dict__ that is NOT in this set and
# does not start with "_" is treated as a user-supplied extra field (i.e. it
# was passed via logger.info("msg", extra={"key": "value"})) and is merged
# into the emitted JSON object.
#
# Reference: https://docs.python.org/3/library/logging.html#logrecord-attributes
_STANDARD_LOG_RECORD_ATTRS: frozenset[str] = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "message",
        "module",
        "msecs",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "thread",
        "threadName",
        # Python 3.12+
        "taskName",
    }
)

_RESERVED_LOG_FIELDS: frozenset[str] = frozenset(
    {
        "timestamp",
        "level",
        "logger",
        "message",
        "environment",
        "exception",
    }
)


class JSONFormatter(logging.Formatter):
    """Custom logging formatter that outputs log records as JSON strings.

    Standard fields (timestamp, level, logger, message, environment) are always
    included.  Any fields supplied via ``extra={...}`` in a logging call are
    merged into the JSON output, enabling structured per-event correlation data
    (e.g. event_id, instrument_id, topic, partition).
    """

    def __init__(self, app_env: str = "development") -> None:
        super().__init__()
        self.app_env = app_env

    def format(self, record: logging.LogRecord) -> str:
        log_object: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "environment": self.app_env,
        }

        if record.exc_info:
            log_object["exception"] = self.formatException(record.exc_info)

        # Merge user-supplied extra fields into the JSON output.
        # Skip standard LogRecord attributes, private/internal keys (starting
        # with "_"), and reserved output fields to prevent collision.
        extra_fields = {
            k: v
            for k, v in record.__dict__.items()
            if k not in _STANDARD_LOG_RECORD_ATTRS
            and not k.startswith("_")
            and k not in _RESERVED_LOG_FIELDS
        }
        if extra_fields:
            log_object.update(extra_fields)

        return json.dumps(log_object)


def setup_logging(log_level: str = "INFO", app_env: str = "development") -> None:
    """Configure root logger with structured JSON formatting."""
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level.upper())

    # Clear existing handlers to avoid duplication
    root_logger.handlers.clear()

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JSONFormatter(app_env=app_env))
    root_logger.addHandler(handler)
