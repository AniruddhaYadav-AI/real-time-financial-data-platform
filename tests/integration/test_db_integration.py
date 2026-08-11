import uuid
from collections.abc import AsyncGenerator
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any

import pytest
from alembic.config import Config
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from alembic import command
from financial_platform.database.models.instruments import Instrument
from financial_platform.database.models.market_data import MarketTrade


@pytest.fixture(scope="session")
def postgres_container():
    from testcontainers.community.postgres import PostgresContainer
    # Set up the postgres container
    with PostgresContainer("postgres:16-alpine") as postgres:
        yield postgres

@pytest.fixture(scope="session")
def database_url(postgres_container):
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    user = postgres_container.username
    password = postgres_container.password
    dbname = postgres_container.dbname
    return f"postgresql+asyncpg://{user}:{password}@{host}:{port}/{dbname}"

@pytest.fixture(scope="function")
async def engine(database_url: str) -> AsyncGenerator[Any, None]:
    engine = create_async_engine(database_url, pool_pre_ping=True)
    yield engine
    await engine.dispose()

@pytest.fixture(scope="session")
def alembic_config(database_url):
    # Prepare alembic config
    alembic_cfg = Config("alembic.ini")
    alembic_cfg.set_main_option("sqlalchemy.url", database_url)
    return alembic_cfg

@pytest.fixture(scope="session", autouse=True)
def setup_database(alembic_config):
    # Run migrations using alembic
    command.upgrade(alembic_config, "head")
    yield
    command.downgrade(alembic_config, "base")
    # Verify we can upgrade again after downgrade
    command.upgrade(alembic_config, "head")

@pytest.fixture
async def db_session(engine: Any) -> AsyncGenerator[AsyncSession, None]:
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

@pytest.mark.asyncio
async def test_database_connectivity(engine: Any) -> None:
    async with engine.connect() as conn:
        result = await conn.execute(text("SELECT 1"))
        assert result.scalar() == 1

@pytest.mark.asyncio
async def test_instrument_uniqueness(db_session: AsyncSession) -> None:
    inst1 = Instrument(venue="Binance", symbol="BTC/USDT", asset_class="crypto")
    db_session.add(inst1)
    await db_session.commit()

    inst2 = Instrument(venue="Binance", symbol="BTC/USDT", asset_class="crypto")
    db_session.add(inst2)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

@pytest.mark.asyncio
async def test_foreign_key_enforcement(db_session: AsyncSession) -> None:
    now = datetime.now(UTC)
    trade = MarketTrade(
        instrument_id=uuid.uuid4(),  # Random UUID, nonexistent instrument
        exchange_trade_id="fk-fail-trade",
        price=Decimal("100"),
        volume=Decimal("1"),
        event_time=now,
        received_at=now
    )
    db_session.add(trade)
    with pytest.raises(IntegrityError):
        await db_session.commit()
    await db_session.rollback()

@pytest.mark.asyncio
async def test_trade_uniqueness_idempotency(db_session: AsyncSession) -> None:
    inst = Instrument(venue="Coinbase", symbol="ETH/USD", asset_class="crypto")
    db_session.add(inst)
    await db_session.commit()

    now = datetime.now(UTC)
    trade = MarketTrade(
        instrument_id=inst.id,
        exchange_trade_id="trade-123",
        price=Decimal("3000.50"),
        volume=Decimal("1.5"),
        event_time=now,
        received_at=now
    )
    db_session.add(trade)
    await db_session.commit()

    # Idempotency via ON CONFLICT DO NOTHING
    stmt = text("""
        INSERT INTO market_trades (
            id, instrument_id, exchange_trade_id, price, volume, event_time, received_at
        )
        VALUES (:id, :instrument_id, :exchange_trade_id, :price, :volume, :event_time, :received_at)
        ON CONFLICT (instrument_id, exchange_trade_id) DO NOTHING
    """)
    await db_session.execute(stmt, {
        "id": uuid.uuid4(),
        "instrument_id": inst.id,
        "exchange_trade_id": "trade-123",
        "price": Decimal("3000.50"),
        "volume": Decimal("1.5"),
        "event_time": now,
        "received_at": now
    })
    await db_session.commit()

    # Verify only one record exists
    result = await db_session.execute(text(
        "SELECT COUNT(*) FROM market_trades WHERE exchange_trade_id = 'trade-123'"
    ))
    assert result.scalar() == 1

@pytest.mark.asyncio
async def test_ohlcv_upsert_behavior(db_session: AsyncSession) -> None:
    inst = Instrument(venue="Kraken", symbol="SOL/USD", asset_class="crypto")
    db_session.add(inst)
    await db_session.commit()

    now = datetime.now(UTC)

    # Insert OHLCV
    stmt_insert = text("""
        INSERT INTO market_ohlcv (
            instrument_id, timeframe, window_start, open, high, low, close, volume
        )
        VALUES (:instrument_id, :timeframe, :window_start, :open, :high, :low, :close, :volume)
    """)
    await db_session.execute(stmt_insert, {
        "instrument_id": inst.id,
        "timeframe": "1m",
        "window_start": now,
        "open": Decimal("100"),
        "high": Decimal("105"),
        "low": Decimal("99"),
        "close": Decimal("102"),
        "volume": Decimal("10")
    })
    await db_session.commit()

    # UPSERT with changed values
    stmt_upsert = text("""
        INSERT INTO market_ohlcv (
            instrument_id, timeframe, window_start, open, high, low, close, volume
        )
        VALUES (:instrument_id, :timeframe, :window_start, :open, :high, :low, :close, :volume)
        ON CONFLICT (instrument_id, timeframe, window_start)
        DO UPDATE SET
            open = EXCLUDED.open,
            high = EXCLUDED.high,
            low = EXCLUDED.low,
            close = EXCLUDED.close,
            volume = EXCLUDED.volume
    """)
    await db_session.execute(stmt_upsert, {
        "instrument_id": inst.id,
        "timeframe": "1m",
        "window_start": now,
        "open": Decimal("100"),
        "high": Decimal("106"),
        "low": Decimal("99"),
        "close": Decimal("103"),
        "volume": Decimal("15")
    })
    await db_session.commit()

    # Verify updated
    result = await db_session.execute(
        text("SELECT high, close, volume FROM market_ohlcv WHERE instrument_id = :inst"),
        {"inst": inst.id}
    )
    row = result.fetchone()
    assert row is not None
    assert row.high == Decimal("106")
    assert row.close == Decimal("103")
    assert row.volume == Decimal("15")

@pytest.mark.asyncio
async def test_transaction_rollback(db_session: AsyncSession) -> None:
    inst = Instrument(venue="Bitfinex", symbol="XRP/USD", asset_class="crypto")
    db_session.add(inst)
    await db_session.commit()

    # Start a transaction and force a rollback
    try:
        async with db_session.begin():
            trade = MarketTrade(
                instrument_id=inst.id,
                exchange_trade_id="bad-trade",
                price=Decimal("1.0"),
                volume=Decimal("100"),
                event_time=datetime.now(UTC),
                received_at=datetime.now(UTC)
            )
            db_session.add(trade)
            # Raise exception to trigger rollback
            raise ValueError("Intentional failure")
    except ValueError:
        pass

    # Verify trade was not saved
    result = await db_session.execute(text(
        "SELECT COUNT(*) FROM market_trades WHERE exchange_trade_id = 'bad-trade'"
    ))
    assert result.scalar() == 0
