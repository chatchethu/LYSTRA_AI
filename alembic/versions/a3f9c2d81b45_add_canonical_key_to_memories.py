"""add canonical_key to memories

Revision ID: a3f9c2d81b45
Revises: 7bae7aef7734
Create Date: 2026-09-11 23:35:00.000000

The Memory SQLAlchemy model defines canonical_key but it was never added to
any migration, so the column is absent from the live database.
This migration adds it with a nullable String type + index (matching the model).
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a3f9c2d81b45'
down_revision: Union[str, None] = '7bae7aef7734'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add the column as nullable so it works on a table with existing rows
    op.add_column(
        'memories',
        sa.Column('canonical_key', sa.String(), nullable=True)
    )
    # Add the index (matches the model's index=True on canonical_key)
    op.create_index(
        op.f('ix_memories_canonical_key'),
        'memories',
        ['canonical_key'],
        unique=False
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_memories_canonical_key'), table_name='memories')
    op.drop_column('memories', 'canonical_key')
