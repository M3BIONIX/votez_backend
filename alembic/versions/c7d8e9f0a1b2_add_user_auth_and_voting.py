"""Add user authentication, likes, votes and created_by to polls

Revision ID: c7d8e9f0a1b2
Revises: a1b2c3d4e5f6
Create Date: 2025-12-30 12:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema - add authentication, likes, votes and created_by."""
    
    # Add hashed_password to users table
    op.add_column('users', 
        sa.Column('hashed_password', sa.String(length=255), nullable=True)
    )
    
    # Add created_by to poll table
    op.add_column('poll',
        sa.Column('created_by', sa.Integer(), nullable=True)
    )
    op.create_foreign_key(
        'fk_poll_created_by',
        'poll', 'users',
        ['created_by'], ['id']
    )
    
    # Create likes table
    op.create_table('likes',
        sa.Column('poll_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('id', sa.Integer(), server_default=sa.text("nextval('id_seq')"), nullable=False),
        sa.Column('uuid', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.ForeignKeyConstraint(['poll_id'], ['poll.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('poll_id', 'user_id', name='uq_likes_poll_user')
    )
    
    # Create votes table
    op.create_table('votes',
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('poll_id', sa.Integer(), nullable=False),
        sa.Column('option_id', sa.Integer(), nullable=False),
        sa.Column('id', sa.Integer(), server_default=sa.text("nextval('id_seq')"), nullable=False),
        sa.Column('uuid', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.ForeignKeyConstraint(['poll_id'], ['poll.id'], ),
        sa.ForeignKeyConstraint(['option_id'], ['poll_options.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema - remove authentication, likes, votes and created_by."""
    
    # Drop votes table
    op.drop_table('votes')
    
    # Drop likes table
    op.drop_table('likes')
    
    # Remove created_by from poll table
    op.drop_constraint('fk_poll_created_by', 'poll', type_='foreignkey')
    op.drop_column('poll', 'created_by')
    
    # Remove hashed_password from users table
    op.drop_column('users', 'hashed_password')

