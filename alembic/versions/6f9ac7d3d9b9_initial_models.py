"""Initial Models

Revision ID: 6f9ac7d3d9b9
Revises: 
Create Date: 2025-10-26 08:45:54.522408
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.schema import CreateSequence, DropSequence, Sequence as SQLASequence

revision: str = '6f9ac7d3d9b9'
down_revision: Union[str, Sequence, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Create the sequence ONCE - before any tables
    op.execute(CreateSequence(SQLASequence('id_seq', start=1000)))

    # Now create all your tables
    op.create_table('poll',
        sa.Column('title', sa.String(length=50), nullable=False),
        sa.Column('likes', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.Column('id', sa.Integer(), server_default=sa.text("nextval('id_seq')"), nullable=False),
        sa.Column('uuid', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('users',
        sa.Column('name', sa.String(length=50), nullable=False),
        sa.Column('email', sa.String(length=50), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('id', sa.Integer(), server_default=sa.text("nextval('id_seq')"), nullable=False),
        sa.Column('uuid', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email')
    )

    op.create_table('poll_options',
        sa.Column('poll_id', sa.Integer(), nullable=False),
        sa.Column('option_name', sa.String(length=50), nullable=False),
        sa.Column('votes', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=False),
        sa.Column('version_id', sa.Integer(), server_default='1', nullable=False),
        sa.Column('id', sa.Integer(), server_default=sa.text("nextval('id_seq')"), nullable=False),
        sa.Column('uuid', sa.UUID(), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.ForeignKeyConstraint(['poll_id'], ['poll.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    """Downgrade schema."""
    # Drop tables first
    op.drop_table('poll_options')
    op.drop_table('users')
    op.drop_table('poll')

    # Drop sequence last
    op.execute(DropSequence(SQLASequence('id_seq')))
