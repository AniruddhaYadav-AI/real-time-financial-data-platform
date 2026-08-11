"""initial_migration

Revision ID: 609977151e4b
Revises:
Create Date: 2026-08-11 14:33:09.390464

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '609977151e4b'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # instruments
    op.create_table('instruments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('venue', sa.String(), nullable=False),
        sa.Column('symbol', sa.String(), nullable=False),
        sa.Column('asset_class', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('venue', 'symbol', name='uq_instrument_venue_symbol')
    )

    # market_trades
    op.create_table('market_trades',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('instrument_id', sa.UUID(), nullable=False),
        sa.Column('exchange_trade_id', sa.String(), nullable=False),
        sa.Column('price', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('volume', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('event_time', sa.DateTime(timezone=True), nullable=False),
        sa.Column('received_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('instrument_id', 'exchange_trade_id', name='uq_trade_instrument_exchange_id')
    )
    op.create_index('ix_market_trades_instrument_time', 'market_trades', ['instrument_id', sa.text('event_time DESC')], unique=False)

    # market_ohlcv
    op.create_table('market_ohlcv',
        sa.Column('instrument_id', sa.UUID(), nullable=False),
        sa.Column('timeframe', sa.String(), nullable=False),
        sa.Column('window_start', sa.DateTime(timezone=True), nullable=False),
        sa.Column('open', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('high', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('low', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('close', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.Column('volume', sa.Numeric(precision=20, scale=8), nullable=False),
        sa.ForeignKeyConstraint(['instrument_id'], ['instruments.id'], ondelete='RESTRICT'),
        sa.PrimaryKeyConstraint('instrument_id', 'timeframe', 'window_start')
    )

def downgrade() -> None:

    op.drop_table('market_ohlcv')
    op.drop_index('ix_market_trades_instrument_time', table_name='market_trades')
    op.drop_table('market_trades')
    op.drop_table('instruments')
