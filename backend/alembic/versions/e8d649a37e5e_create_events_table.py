"""create competitor_events table

Revision ID: e8d649a37e5e
Revises: a9f106260733
Create Date: 2026-05-22 19:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8d649a37e5e'
down_revision: Union[str, None] = 'a9f106260733'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'competitor_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('competitor_id', sa.Integer(), nullable=False),
        sa.Column('event_type', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('original_text_diff', sa.Text(), nullable=True),
        sa.Column('confidence_score', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('severity', sa.String(), nullable=False, server_default='low'),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['competitor_id'], ['competitors.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_competitor_events_id'), 'competitor_events', ['id'], unique=False)
    op.create_index(op.f('ix_competitor_events_event_type'), 'competitor_events', ['event_type'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_competitor_events_event_type'), table_name='competitor_events')
    op.drop_index(op.f('ix_competitor_events_id'), table_name='competitor_events')
    op.drop_table('competitor_events')
