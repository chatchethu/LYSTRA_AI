"""add last_used_at to memories

Revision ID: b5e8f1a23c90
Revises: a3f9c2d81b45
Create Date: 2026-09-11 23:47:00.000000

The crud.memory module writes last_used_at when ranking retrieved memories
(touch_last_used) and update_status, but the column was never added to the
DB. This migration adds it as a nullable TIMESTAMP WITH TIME ZONE column.
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'b5e8f1a23c90'
down_revision: Union[str, None] = 'a3f9c2d81b45'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'memories',
        sa.Column('last_used_at', sa.DateTime(timezone=True), nullable=True)
    )


def downgrade() -> None:
    op.drop_column('memories', 'last_used_at')
