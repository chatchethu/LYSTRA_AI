"""Add MetricEvent model

Revision ID: 002
Revises: 001
Create Date: 2026-09-01 12:20:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('metric_events',
    sa.Column('id', sa.UUID(), nullable=False),
    sa.Column('metric_type', sa.String(), nullable=False),
    sa.Column('value', sa.Float(), nullable=False),
    sa.Column('attributes', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
    sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_metric_events_metric_type'), 'metric_events', ['metric_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_metric_events_metric_type'), table_name='metric_events')
    op.drop_table('metric_events')
