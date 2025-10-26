"""Set NOT NULL constraints for hashed_password and created_by

Revision ID: d9e0f1a2b3c4
Revises: c7d8e9f0a1b2
Create Date: 2025-12-30 12:30:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = 'd9e0f1a2b3c4'
down_revision: Union[str, None] = 'c7d8e9f0a1b2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Set NOT NULL constraints for hashed_password and created_by."""
    op.alter_column('users', 'hashed_password',
        existing_type=sa.String(255),
        nullable=False
    )

    op.alter_column('poll', 'created_by',
        existing_type=sa.Integer(),
        nullable=False
    )


def downgrade() -> None:
    """Remove NOT NULL constraints from hashed_password and created_by."""
    
    op.alter_column('poll', 'created_by',
        existing_type=sa.Integer(),
        nullable=True
    )
    
    op.alter_column('users', 'hashed_password',
        existing_type=sa.String(255),
        nullable=True
    )

