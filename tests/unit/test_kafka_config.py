"""Unit tests for KafkaSettings configuration.

These tests verify defaults, environment-variable overrides, type correctness,
and that the producer_config / consumer_config properties produce dicts with
all keys required by librdkafka / confluent-kafka.

No broker connection or Docker dependency — pure in-process tests.
"""

import pytest

from financial_platform.events.config import KafkaSettings

# ── Default values ────────────────────────────────────────────────────────────


def test_kafka_settings_default_bootstrap_servers() -> None:
    """Default bootstrap server points to the local Redpanda external listener."""
    settings = KafkaSettings()
    assert settings.KAFKA_BOOTSTRAP_SERVERS == "localhost:19092"


def test_kafka_settings_default_trade_topic() -> None:
    """Default trade topic matches the architecture specification."""
    settings = KafkaSettings()
    assert settings.KAFKA_TRADE_TOPIC == "market.trades.raw"


def test_kafka_settings_default_dlq_topic() -> None:
    """Default DLQ topic matches the architecture specification."""
    settings = KafkaSettings()
    assert settings.KAFKA_DLQ_TOPIC == "dlq.market.trades"


def test_kafka_settings_default_consumer_group() -> None:
    """Default consumer group ID is trade-processor."""
    settings = KafkaSettings()
    assert settings.KAFKA_CONSUMER_GROUP_ID == "trade-processor"


def test_kafka_settings_default_trade_topic_partitions() -> None:
    """Trade topic defaults to 3 partitions (development value)."""
    settings = KafkaSettings()
    assert settings.KAFKA_TRADE_TOPIC_PARTITIONS == 3


def test_kafka_settings_default_dlq_topic_partitions() -> None:
    """DLQ topic defaults to 1 partition (development value)."""
    settings = KafkaSettings()
    assert settings.KAFKA_DLQ_TOPIC_PARTITIONS == 1


# ── Critical safety defaults ──────────────────────────────────────────────────


def test_kafka_settings_acks_default_is_all() -> None:
    """Producer acks defaults to 'all' for maximum durability."""
    settings = KafkaSettings()
    assert settings.KAFKA_ACKS == "all"


def test_kafka_settings_idempotence_enabled_by_default() -> None:
    """Producer idempotence is enabled by default to prevent duplicate delivery."""
    settings = KafkaSettings()
    assert settings.KAFKA_ENABLE_IDEMPOTENCE is True


def test_kafka_settings_auto_commit_disabled_by_default() -> None:
    """Auto-commit MUST be False to enforce manual offset management."""
    settings = KafkaSettings()
    assert settings.KAFKA_ENABLE_AUTO_COMMIT is False


def test_kafka_settings_auto_offset_reset_is_earliest() -> None:
    """Consumer defaults to earliest to avoid missing events on new group start."""
    settings = KafkaSettings()
    assert settings.KAFKA_AUTO_OFFSET_RESET == "earliest"


# ── Type correctness ──────────────────────────────────────────────────────────


def test_kafka_settings_partition_counts_are_integers() -> None:
    """Topic partition counts are typed as int, not str."""
    settings = KafkaSettings()
    assert isinstance(settings.KAFKA_TRADE_TOPIC_PARTITIONS, int)
    assert isinstance(settings.KAFKA_DLQ_TOPIC_PARTITIONS, int)


def test_kafka_settings_timeout_values_are_integers() -> None:
    """All millisecond timeout fields are typed as int."""
    settings = KafkaSettings()
    assert isinstance(settings.KAFKA_SESSION_TIMEOUT_MS, int)
    assert isinstance(settings.KAFKA_MAX_POLL_INTERVAL_MS, int)
    assert isinstance(settings.KAFKA_DELIVERY_TIMEOUT_MS, int)


def test_kafka_settings_boolean_fields_are_bool() -> None:
    """Boolean fields are typed as bool (not str '0'/'1')."""
    settings = KafkaSettings()
    assert isinstance(settings.KAFKA_ENABLE_IDEMPOTENCE, bool)
    assert isinstance(settings.KAFKA_ENABLE_AUTO_COMMIT, bool)


# ── Environment variable overrides ───────────────────────────────────────────


def test_kafka_settings_bootstrap_servers_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KAFKA_BOOTSTRAP_SERVERS env var overrides the default."""
    monkeypatch.setenv("KAFKA_BOOTSTRAP_SERVERS", "broker1:9092,broker2:9092")
    settings = KafkaSettings()
    assert settings.KAFKA_BOOTSTRAP_SERVERS == "broker1:9092,broker2:9092"


def test_kafka_settings_consumer_group_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KAFKA_CONSUMER_GROUP_ID env var overrides the default."""
    monkeypatch.setenv("KAFKA_CONSUMER_GROUP_ID", "test-consumer-group")
    settings = KafkaSettings()
    assert settings.KAFKA_CONSUMER_GROUP_ID == "test-consumer-group"


def test_kafka_settings_trade_topic_env_override(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """KAFKA_TRADE_TOPIC env var overrides the default."""
    monkeypatch.setenv("KAFKA_TRADE_TOPIC", "custom.trades.raw")
    settings = KafkaSettings()
    assert settings.KAFKA_TRADE_TOPIC == "custom.trades.raw"


# ── producer_config property ─────────────────────────────────────────────────


def test_producer_config_contains_required_keys() -> None:
    """producer_config has all keys required by librdkafka / AIOProducer."""
    config = KafkaSettings().producer_config
    assert "bootstrap.servers" in config
    assert "acks" in config
    assert "enable.idempotence" in config
    assert "delivery.timeout.ms" in config
    assert "client.id" in config


def test_producer_config_bootstrap_servers_matches_setting() -> None:
    """producer_config['bootstrap.servers'] reflects KAFKA_BOOTSTRAP_SERVERS."""
    settings = KafkaSettings()
    assert settings.producer_config["bootstrap.servers"] == settings.KAFKA_BOOTSTRAP_SERVERS


def test_producer_config_acks_is_all() -> None:
    """producer_config acks value is 'all'."""
    config = KafkaSettings().producer_config
    assert config["acks"] == "all"


def test_producer_config_idempotence_is_true() -> None:
    """producer_config enable.idempotence is True."""
    config = KafkaSettings().producer_config
    assert config["enable.idempotence"] is True


# ── consumer_config property ─────────────────────────────────────────────────


def test_consumer_config_contains_required_keys() -> None:
    """consumer_config has all keys required by librdkafka / AIOConsumer."""
    config = KafkaSettings().consumer_config
    assert "bootstrap.servers" in config
    assert "group.id" in config
    assert "auto.offset.reset" in config
    assert "enable.auto.commit" in config
    assert "enable.auto.offset.store" in config
    assert "session.timeout.ms" in config
    assert "max.poll.interval.ms" in config
    assert "client.id" in config


def test_consumer_config_auto_commit_is_false() -> None:
    """consumer_config enable.auto.commit is False (required for manual offset management)."""
    config = KafkaSettings().consumer_config
    assert config["enable.auto.commit"] is False


def test_consumer_config_auto_offset_store_is_false() -> None:
    """consumer_config enable.auto.offset.store is False for full offset control."""
    config = KafkaSettings().consumer_config
    assert config["enable.auto.offset.store"] is False


def test_consumer_config_group_id_matches_setting() -> None:
    """consumer_config['group.id'] reflects KAFKA_CONSUMER_GROUP_ID."""
    settings = KafkaSettings()
    assert settings.consumer_config["group.id"] == settings.KAFKA_CONSUMER_GROUP_ID


def test_consumer_config_bootstrap_servers_matches_setting() -> None:
    """consumer_config['bootstrap.servers'] reflects KAFKA_BOOTSTRAP_SERVERS."""
    settings = KafkaSettings()
    assert settings.consumer_config["bootstrap.servers"] == settings.KAFKA_BOOTSTRAP_SERVERS
