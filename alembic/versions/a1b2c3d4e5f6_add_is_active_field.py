"""Add is_active field to poll and poll_options

Revision ID: a1b2c3d4e5f6
Revises: 6f9ac7d3d9b9
Create Date: 2025-10-26 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '6f9ac7d3d9b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add is_active column to poll and poll_options tables."""
    # Add is_active column to poll table
    op.add_column('poll', 
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true')
    )
    
    # Add is_active column to poll_options table
    op.add_column('poll_options', 
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true')
    )


def downgrade() -> None:
    """Remove is_active column from poll and poll_options tables."""
    # Remove is_active column from poll_options table
    op.drop_column('poll_options', 'is_active')
    
    # Remove is_active column from poll table
    op.drop_column('poll', 'is_active')

