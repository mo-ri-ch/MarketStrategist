"""create memories table

Revision ID: 9ef3071d0e12
Revises: 7da89c2ef34b
Create Date: 2026-05-22 22:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '9ef3071d0e12'
down_revision: Union[str, None] = '7da89c2ef34b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'memories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('company_id', sa.Integer(), nullable=False),
        sa.Column('key', sa.String(), nullable=False),
        sa.Column('value', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['company_id'], ['companies.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_memories_id'), 'memories', ['id'], unique=False)
    op.create_index(op.f('ix_memories_company_id'), 'memories', ['company_id'], unique=False)
    op.create_index(op.f('ix_memories_key'), 'memories', ['key'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_memories_key'), table_name='memories')
    op.drop_index(op.f('ix_memories_company_id'), table_name='memories')
    op.drop_index(op.f('ix_memories_id'), table_name='memories')
    op.drop_table('memories')
