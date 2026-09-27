"""Add timezone field to users table

Revision ID: 003
Revises: 002
Create Date: 2026-09-27

Each user stores their preferred IANA timezone string (e.g. "Asia/Kolkata").
Lystra uses this to display time in the user's local timezone rather than
always showing UTC or the server's local clock.
"""
from typing import Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'users',
        sa.Column(
            'timezone',
            sa.String(length=64),
            nullable=True,
            comment='IANA timezone string, e.g. Asia/Kolkata. NULL defaults to UTC.'
        )
    )


def downgrade() -> None:
    op.drop_column('users', 'timezone')
