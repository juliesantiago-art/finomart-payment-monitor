"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2026-03-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'payment_methods',
        sa.Column('id', sa.String(64), primary_key=True),
        sa.Column('name', sa.String(128), nullable=False),
        sa.Column('type', sa.String(32), nullable=False),
        sa.Column('country', sa.String(4), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
    )

    op.create_table(
        'integration_costs',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('payment_method_id', sa.String(64), sa.ForeignKey('payment_methods.id'), nullable=False),
        sa.Column('monthly_fee_usd', sa.Float(), default=0.0),
        sa.Column('per_transaction_fee_usd', sa.Float(), default=0.0),
        sa.Column('effective_from', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column('payment_method_id', sa.String(64), sa.ForeignKey('payment_methods.id'), nullable=False),
        sa.Column('country', sa.String(4), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(8), nullable=False),
        sa.Column('usd_amount', sa.Float(), nullable=False),
        sa.Column('net_revenue_usd', sa.Float(), default=0.0),
        sa.Column('status', sa.String(16), nullable=False),
        sa.Column('chargeback_flag', sa.Boolean(), default=False),
        sa.Column('settlement_speed_days', sa.Integer(), nullable=True),
        sa.Column('fx_spread_pct', sa.Float(), nullable=True),
        sa.Column('installment_count', sa.Integer(), default=1),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )

    op.create_index('ix_transactions_payment_method_id', 'transactions', ['payment_method_id'])
    op.create_index('ix_transactions_country', 'transactions', ['country'])
    op.create_index('ix_transactions_status', 'transactions', ['status'])
    op.create_index('ix_transactions_created_at', 'transactions', ['created_at'])


def downgrade() -> None:
    op.drop_table('transactions')
    op.drop_table('integration_costs')
    op.drop_table('payment_methods')
