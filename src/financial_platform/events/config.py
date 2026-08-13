"""Kafka/Redpanda configuration settings for the financial data platform."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class KafkaSettings(BaseSettings):
    """Kafka/Redpanda configuration loaded from environment variables or .env file.

    All fields follow the KAFKA_ prefix convention and map 1:1 to environment
    variables.  The ``producer_config`` and ``consumer_config`` properties return
    librdkafka-compatible configuration dicts ready to be passed to
    ``AIOProducer`` / ``AIOConsumer``.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # ── Broker ──────────────────────────────────────────────────────────────
    KAFKA_BOOTSTRAP_SERVERS: str = "localhost:19092"

    # ── Topics ──────────────────────────────────────────────────────────────
    KAFKA_TRADE_TOPIC: str = "market.trades.raw"
    KAFKA_DLQ_TOPIC: str = "dlq.market.trades"

    # Development-only partition counts.
    # Production partition count MUST be determined empirically via load testing.
    KAFKA_TRADE_TOPIC_PARTITIONS: int = 3
    KAFKA_DLQ_TOPIC_PARTITIONS: int = 1

    # ── Consumer group ───────────────────────────────────────────────────────
    KAFKA_CONSUMER_GROUP_ID: str = "trade-processor"

    # ── Producer settings ────────────────────────────────────────────────────
    KAFKA_ACKS: str = "all"
    KAFKA_ENABLE_IDEMPOTENCE: bool = True
    KAFKA_DELIVERY_TIMEOUT_MS: int = 120000

    # ── Consumer settings ────────────────────────────────────────────────────
    # auto.offset.reset: start from earliest unread offset when no committed
    # offset exists for the consumer group.
    KAFKA_AUTO_OFFSET_RESET: str = "earliest"

    # CRITICAL: auto-commit MUST be disabled.  Offsets are committed manually
    # *after* successful processing to enforce the process-before-commit rule.
    KAFKA_ENABLE_AUTO_COMMIT: bool = False

    KAFKA_SESSION_TIMEOUT_MS: int = 45000
    KAFKA_MAX_POLL_INTERVAL_MS: int = 300000

    # ── Config properties ────────────────────────────────────────────────────

    @property
    def producer_config(self) -> dict[str, object]:
        """Return a librdkafka-compatible producer configuration dict.

        Suitable for passing directly to ``confluent_kafka.aio.AIOProducer``.
        """
        return {
            "bootstrap.servers": self.KAFKA_BOOTSTRAP_SERVERS,
            "acks": self.KAFKA_ACKS,
            "enable.idempotence": self.KAFKA_ENABLE_IDEMPOTENCE,
            "delivery.timeout.ms": self.KAFKA_DELIVERY_TIMEOUT_MS,
            "client.id": "financial-platform-producer",
        }

    @property
    def consumer_config(self) -> dict[str, object]:
        """Return a librdkafka-compatible consumer configuration dict.

        Suitable for passing directly to ``confluent_kafka.aio.AIOConsumer``.
        """
        return {
            "bootstrap.servers": self.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": self.KAFKA_CONSUMER_GROUP_ID,
            "auto.offset.reset": self.KAFKA_AUTO_OFFSET_RESET,
            "enable.auto.commit": self.KAFKA_ENABLE_AUTO_COMMIT,
            "enable.auto.offset.store": False,
            "session.timeout.ms": self.KAFKA_SESSION_TIMEOUT_MS,
            "max.poll.interval.ms": self.KAFKA_MAX_POLL_INTERVAL_MS,
            "client.id": "financial-platform-consumer",
        }


kafka_settings = KafkaSettings()
